import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';
import { cookies } from 'next/headers';

export async function GET() {
  try {
    const cookieStore = cookies();
    const supabaseClient = supabase;

    const { data: { session }, error: authError } = await supabaseClient.auth.getSession();
    
    if (authError || !session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { data: profile, error: profileError } = await supabaseClient
      .from('profiles')
      .select('*')
      .eq('id', session.user.id)
      .single();

    if (profileError) {
      return NextResponse.json({ error: profileError.message }, { status: 500 });
    }

    return NextResponse.json(profile);
  } catch (error) {
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

export async function PUT(request: Request) {
  try {
    const cookieStore = cookies();
    const supabaseClient = supabase;
    const body = await request.json();

    const { data: { session }, error: authError } = await supabaseClient.auth.getSession();
    
    if (authError || !session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Validate required fields
    const { full_name, avatar_url, role } = body;
    if (!full_name) {
      return NextResponse.json({ error: 'Full name is required' }, { status: 400 });
    }

    const updateData = {
      id: session.user.id,
      full_name,
      avatar_url: avatar_url || null,
      role: role || 'user',
      updated_at: new Date().toISOString()
    };

    const { data: profile, error: profileError } = await supabaseClient
      .from('profiles')
      .upsert(updateData)
      .select()
      .single();

    if (profileError) {
      return NextResponse.json({ error: profileError.message }, { status: 500 });
    }

    return NextResponse.json(profile);
  } catch (error) {
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
