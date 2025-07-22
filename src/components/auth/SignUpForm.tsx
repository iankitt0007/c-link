import { useState } from 'react';
import { createClient } from '@supabase/supabase-js';

function useAuth() {
  // Initialize Supabase client
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL || '',
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''
  );

  const signUp = async (email: string, password: string, metadata?: object) => {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: metadata
        }
      });
      return { data, error };
    } catch (error) {
      return { data: null, error };
    }
  };

  const signInWithGoogle = async () => {
    try {
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google'
      });
      return { data, error };
    } catch (error) {
      return { data: null, error };
    }
  };

  return {
    signUp,
    signInWithGoogle
  };
}

export default useAuth;

