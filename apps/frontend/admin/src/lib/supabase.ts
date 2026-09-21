import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || import.meta.env.NEXT_PUBLIC_SUPABASE_URL || 'https://culeiqroofltvizgfzim.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || import.meta.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN1bGVpcXJvb2ZsdHZpemdmemltIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkwMTMwMjAsImV4cCI6MjEwNDU4OTAyMH0.DKY8-NcaG5jm81WYm7HtFGtdesLQhKjseJt4gTXO3pU';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
