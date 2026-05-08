-- Political Simulator: Republic in Crisis — Supabase schema
-- Paste this entire file into Supabase Studio → SQL Editor → Run

-- ===========================================
-- 1) The saves table
-- ===========================================
create table if not exists public.saves (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  slot integer not null check (slot >= 1 and slot <= 10),
  name text default '',
  turn integer default 1,
  game_date text default '',
  state_json jsonb not null,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (user_id, slot)
);

create index if not exists saves_user_id_idx on public.saves(user_id);

-- ===========================================
-- 2) Auto-update updated_at on every change
-- ===========================================
create or replace function public.touch_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists saves_touch_updated_at on public.saves;
create trigger saves_touch_updated_at
  before update on public.saves
  for each row execute function public.touch_updated_at();

-- ===========================================
-- 3) Row Level Security: each user only sees their own saves
-- ===========================================
alter table public.saves enable row level security;

drop policy if exists "Users see own saves"   on public.saves;
drop policy if exists "Users insert own saves" on public.saves;
drop policy if exists "Users update own saves" on public.saves;
drop policy if exists "Users delete own saves" on public.saves;

create policy "Users see own saves"
  on public.saves for select
  using (auth.uid() = user_id);

create policy "Users insert own saves"
  on public.saves for insert
  with check (auth.uid() = user_id);

create policy "Users update own saves"
  on public.saves for update
  using (auth.uid() = user_id);

create policy "Users delete own saves"
  on public.saves for delete
  using (auth.uid() = user_id);
