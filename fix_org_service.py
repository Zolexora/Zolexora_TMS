import re

filepath = "apps/backend/app/modules/identity/organisations/service.py"
with open(filepath, "r") as f:
    content = f.read()

# Replace the role query and usage in create_organisation
content = re.sub(
    r'    # 2\. Query Commander role\n.*?raise HTTPException\([^)]+\)\n',
    '',
    content,
    flags=re.DOTALL
)

# Replace member creation
member_creation = """    # 4. Assign initial creator as Commander
    member = OrganisationMember(
        id=uuid.uuid4(),
        organisation_id=org_id,
        user_id=user_id,
        role_id=commander_role.id,
        status=MemberStatus.ACTIVE,
    )"""

new_member_creation = """    # 4. Assign initial creator
    member = OrganisationMember(
        id=uuid.uuid4(),
        organisation_id=org_id,
        user_id=user_id,
        status=MemberStatus.ACTIVE,
        is_creator=True,
    )"""
content = content.replace(member_creation, new_member_creation)

# In list_organisation_members: remove role join
list_members_old = """    stmt = (
        select(OrganisationMember, Role)
        .join(Role, Role.id == OrganisationMember.role_id)
        .where(OrganisationMember.organisation_id == org_id)
        .order_by(OrganisationMember.created_at.asc())
    )
    res = await db.execute(stmt)
    rows = res.all()

    members = []
    for member, role in rows:
        members.append(
            MemberResponse(
                id=member.id,
                organisation_id=member.organisation_id,
                user_id=member.user_id,
                role_code=role.code,
                role_name=role.name,
                status=member.status,
                created_at=member.created_at,
            )
        )"""

list_members_new = """    stmt = (
        select(OrganisationMember)
        .where(OrganisationMember.organisation_id == org_id)
        .order_by(OrganisationMember.created_at.asc())
    )
    res = await db.execute(stmt)
    rows = res.scalars().all()

    members = []
    for member in rows:
        members.append(
            MemberResponse(
                id=member.id,
                organisation_id=member.organisation_id,
                user_id=member.user_id,
                status=member.status,
                created_at=member.created_at,
                is_creator=member.is_creator,
            )
        )"""
content = content.replace(list_members_old, list_members_new)

# In invite_member: remove role references
invite_member_old = """    # Find role
    role_stmt = select(Role).where(Role.code == req.role_code)
    role_res = await db.execute(role_stmt)
    target_role = role_res.scalars().first()
    if not target_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{req.role_code}' does not exist",
        )

    # In a real invite flow, we create an invitation token or placeholder user
    invited_user_id = uuid.uuid4()
    member = OrganisationMember(
        id=uuid.uuid4(),
        organisation_id=org_id,
        user_id=invited_user_id,
        role_id=target_role.id,
        status=MemberStatus.INVITED,
    )
    db.add(member)


    await db.commit()
    await db.refresh(member)

    return MemberResponse(
        id=member.id,
        organisation_id=member.organisation_id,
        user_id=member.user_id,
        role_code=target_role.code,
        role_name=target_role.name,
        status=member.status,
        created_at=member.created_at,
    )"""

invite_member_new = """    import datetime, secrets
    from app.modules.identity.organisations.membership_models import OrganisationInvitation
    
    # Check if user already invited
    existing_invite_stmt = select(OrganisationInvitation).where(
        OrganisationInvitation.organisation_id == org_id,
        OrganisationInvitation.email == req.email,
        OrganisationInvitation.status == "PENDING"
    )
    existing = (await db.execute(existing_invite_stmt)).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="User already invited")
        
    token = secrets.token_urlsafe(32)
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    
    invitation = OrganisationInvitation(
        id=uuid.uuid4(),
        organisation_id=org_id,
        email=req.email,
        token=token,
        status="PENDING",
        expires_at=expires_at,
        created_by=actor_id
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    return {"message": "Invitation sent successfully", "invitation_id": invitation.id}"""
content = content.replace(invite_member_old, invite_member_new)

# In create_organisation, we also need to fix `existing_membership.role.code`
content = content.replace('role_code=existing_membership.role.code if existing_membership.role else "COMMANDER",', 'role_code="CREATOR" if existing_membership.is_creator else "MEMBER",')

with open(filepath, "w") as f:
    f.write(content)
