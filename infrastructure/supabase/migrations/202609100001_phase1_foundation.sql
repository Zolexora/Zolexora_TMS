create extension if not exists pgcrypto;

create schema if not exists private;

create table if not exists public.organisations (
  id uuid primary key default gen_random_uuid(),
  name text not null check (length(trim(name)) between 2 and 160),
  organisation_type text not null check (length(trim(organisation_type)) between 2 and 120),
  status text not null default 'ACTIVE' check (status in ('ACTIVE', 'SUSPENDED', 'ARCHIVED')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text not null check (length(trim(full_name)) between 2 and 160),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.roles (
  id uuid primary key default gen_random_uuid(),
  code text not null unique check (code ~ '^[A-Z][A-Z0-9_]+$'),
  name text not null,
  description text,
  is_system boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.permissions (
  id uuid primary key default gen_random_uuid(),
  code text not null unique check (code ~ '^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$'),
  description text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.role_permissions (
  role_id uuid not null references public.roles(id) on delete cascade,
  permission_id uuid not null references public.permissions(id) on delete cascade,
  primary key (role_id, permission_id)
);

create table if not exists public.organisation_members (
  id uuid primary key default gen_random_uuid(),
  organisation_id uuid not null references public.organisations(id) on delete restrict,
  user_id uuid not null references auth.users(id) on delete restrict,
  role_id uuid not null references public.roles(id) on delete restrict,
  status text not null default 'ACTIVE' check (status in ('ACTIVE', 'INVITED', 'SUSPENDED')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (organisation_id, user_id)
);

create table if not exists public.audit_logs (
  id uuid primary key default gen_random_uuid(),
  organisation_id uuid references public.organisations(id) on delete set null,
  actor_user_id uuid references auth.users(id) on delete set null,
  action text not null,
  entity_type text not null,
  entity_id uuid,
  metadata jsonb not null default '{}'::jsonb,
  ip_address inet,
  user_agent text,
  created_at timestamptz not null default now()
);

create index if not exists organisation_members_user_idx on public.organisation_members(user_id);
create index if not exists organisation_members_organisation_idx on public.organisation_members(organisation_id);
create index if not exists audit_logs_organisation_created_idx on public.audit_logs(organisation_id, created_at desc);

insert into public.roles (code, name, description)
values ('COMMANDER', 'Commander', 'Primary administrative authority for an organisation.')
on conflict (code) do nothing;

insert into public.permissions (code, description)
values
  ('organisation.manage', 'Manage organisation settings.'),
  ('users.manage', 'Manage organisation users.'),
  ('roles.manage', 'Manage organisation roles.'),
  ('booking.create', 'Create bookings.'),
  ('booking.read', 'Read bookings.'),
  ('booking.update', 'Update bookings.'),
  ('duty.create', 'Create duties.'),
  ('duty.read', 'Read duties.'),
  ('duty.assign', 'Assign duties.'),
  ('trip.read', 'Read trips.'),
  ('trip.complete', 'Complete trips.'),
  ('reports.read', 'Read reports.')
on conflict (code) do nothing;

insert into public.role_permissions (role_id, permission_id)
select r.id, p.id
from public.roles r
cross join public.permissions p
where r.code = 'COMMANDER'
on conflict do nothing;

create or replace function private.is_active_member(target_organisation_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.organisation_members member
    where member.organisation_id = target_organisation_id
      and member.user_id = (select auth.uid())
      and member.status = 'ACTIVE'
  );
$$;

create or replace function private.has_organisation_permission(target_organisation_id uuid, required_permission text)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.organisation_members member
    join public.role_permissions role_permission on role_permission.role_id = member.role_id
    join public.permissions permission on permission.id = role_permission.permission_id
    where member.organisation_id = target_organisation_id
      and member.user_id = (select auth.uid())
      and member.status = 'ACTIVE'
      and permission.code = required_permission
  );
$$;

revoke all on function private.is_active_member(uuid) from public;
revoke all on function private.has_organisation_permission(uuid, text) from public;
grant execute on function private.is_active_member(uuid) to authenticated;
grant execute on function private.has_organisation_permission(uuid, text) to authenticated;

create or replace function private.set_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create or replace function private.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, full_name)
  values (
    new.id,
    coalesce(nullif(trim(new.raw_user_meta_data ->> 'full_name'), ''), 'Zolexora user')
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

revoke all on function private.handle_new_user() from public;

create or replace function public.complete_onboarding(organisation_name text, organisation_type text)
returns uuid
language plpgsql
security definer
set search_path = public, private
as $$
declare
  current_user_id uuid := auth.uid();
  commander_role_id uuid;
  new_organisation_id uuid;
begin
  if current_user_id is null then
    raise exception 'Authentication required';
  end if;

  if exists (
    select 1 from public.organisation_members
    where user_id = current_user_id
  ) then
    select organisation_id into new_organisation_id
    from public.organisation_members
    where user_id = current_user_id
    order by created_at
    limit 1;
    return new_organisation_id;
  end if;

  if length(trim(organisation_name)) not between 2 and 160 then
    raise exception 'Organisation name is invalid';
  end if;

  if length(trim(organisation_type)) not between 2 and 120 then
    raise exception 'Organisation type is invalid';
  end if;

  select id into commander_role_id from public.roles where code = 'COMMANDER';

  insert into public.organisations (name, organisation_type)
  values (trim(organisation_name), trim(organisation_type))
  returning id into new_organisation_id;

  insert into public.organisation_members (organisation_id, user_id, role_id)
  values (new_organisation_id, current_user_id, commander_role_id);

  insert into public.audit_logs (organisation_id, actor_user_id, action, entity_type, entity_id)
  values (new_organisation_id, current_user_id, 'ORGANISATION_CREATED', 'organisation', new_organisation_id);

  return new_organisation_id;
end;
$$;

revoke all on function public.complete_onboarding(text, text) from public;
grant execute on function public.complete_onboarding(text, text) to authenticated;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function private.handle_new_user();

drop trigger if exists organisations_set_updated_at on public.organisations;
create trigger organisations_set_updated_at before update on public.organisations
for each row execute function private.set_updated_at();

drop trigger if exists profiles_set_updated_at on public.profiles;
create trigger profiles_set_updated_at before update on public.profiles
for each row execute function private.set_updated_at();

drop trigger if exists organisation_members_set_updated_at on public.organisation_members;
create trigger organisation_members_set_updated_at before update on public.organisation_members
for each row execute function private.set_updated_at();

alter table public.organisations enable row level security;
alter table public.profiles enable row level security;
alter table public.roles enable row level security;
alter table public.permissions enable row level security;
alter table public.role_permissions enable row level security;
alter table public.organisation_members enable row level security;
alter table public.audit_logs enable row level security;

create policy "members can read their organisations"
on public.organisations for select
to authenticated
using ((select private.is_active_member(id)));

create policy "members with permission can update organisations"
on public.organisations for update
to authenticated
using ((select private.has_organisation_permission(id, 'organisation.manage')))
with check ((select private.has_organisation_permission(id, 'organisation.manage')));

create policy "users can read their own profile"
on public.profiles for select
to authenticated
using (id = (select auth.uid()));

create policy "users can update their own profile"
on public.profiles for update
to authenticated
using (id = (select auth.uid()))
with check (id = (select auth.uid()));

create policy "members can read organisation membership"
on public.organisation_members for select
to authenticated
using ((select private.is_active_member(organisation_id)));

create policy "managers can manage organisation membership"
on public.organisation_members for all
to authenticated
using ((select private.has_organisation_permission(organisation_id, 'users.manage')))
with check ((select private.has_organisation_permission(organisation_id, 'users.manage')));

create policy "members can read roles"
on public.roles for select
to authenticated
using (exists (
  select 1 from public.organisation_members member
  where member.user_id = (select auth.uid()) and member.status = 'ACTIVE'
));

create policy "members can read permissions"
on public.permissions for select
to authenticated
using (exists (
  select 1 from public.organisation_members member
  where member.user_id = (select auth.uid()) and member.status = 'ACTIVE'
));

create policy "members can read role permissions"
on public.role_permissions for select
to authenticated
using (exists (
  select 1 from public.organisation_members member
  where member.user_id = (select auth.uid()) and member.status = 'ACTIVE'
));

create policy "members can read audit logs"
on public.audit_logs for select
to authenticated
using ((select private.is_active_member(organisation_id)));

create policy "authenticated users can insert own audit logs"
on public.audit_logs for insert
to authenticated
with check (
  actor_user_id = (select auth.uid())
  and (organisation_id is null or (select private.is_active_member(organisation_id)))
);
