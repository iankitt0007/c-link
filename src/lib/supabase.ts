import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://brlougeuakvyhjnikoip.supabase.co'
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (!supabaseKey) throw new Error('Missing SUPABASE_ANON_KEY environment variable')

export const supabase = createClient(supabaseUrl, supabaseKey)
