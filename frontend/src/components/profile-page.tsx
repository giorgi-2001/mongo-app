import { useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { ArrowUpRight, Database, LogOut, ShieldCheck } from 'lucide-react'
import { Avatar, AvatarFallback } from './ui/avatar'
import { Button } from './ui/button'
import { logoutUser, type UserProfile } from '../lib/auth-api'

export function ProfilePage({ profile }: { profile: UserProfile }) {
  const navigate = useNavigate()
  const [isSigningOut, setIsSigningOut] = useState(false)
  const initials = profile.email.slice(0, 2).toUpperCase()

  async function signOut() {
    setIsSigningOut(true)
    try {
      await logoutUser()
    } catch {
      // The local access token is cleared even if the server cannot be reached.
    }
    await navigate({ to: '/login' })
  }

  return (
    <main className="profile-page">
      <header className="profile-nav">
        <a className="profile-brand" href="/profile" aria-label="Mongo App profile">
          <span className="profile-brand-mark"><Database size={18} /></span>
          <span>Mongo App</span>
        </a>
        <Button className="profile-signout" variant="outline" onClick={signOut} disabled={isSigningOut}>
          <LogOut size={15} />
          <span>{isSigningOut ? 'Signing out...' : 'Sign out'}</span>
        </Button>
      </header>

      <section className="profile-main" aria-labelledby="profile-title">
        <div className="profile-heading">
          <div>
            <p className="profile-eyebrow">Account</p>
            <h1 id="profile-title">Your profile</h1>
            <p className="profile-intro">Your personal details and account status.</p>
          </div>
          <span className={`profile-status ${profile.isActive ? 'is-active' : 'is-inactive'}`}>
            <span />{profile.isActive ? 'Active account' : 'Inactive account'}
          </span>
        </div>

        <div className="profile-identity">
          <Avatar className="profile-avatar" size="lg">
            <AvatarFallback>{initials}</AvatarFallback>
          </Avatar>
          <div className="profile-identity-copy">
            <h2>{profile.email}</h2>
            <p><ShieldCheck size={15} /> Member account</p>
          </div>
        </div>

        <dl className="profile-details">
          <ProfileField label="Email address" value={profile.email} />
          <ProfileField label="Age" value={String(profile.age)} />
          <ProfileField label="Role" value={profile.role} />
          <ProfileField label="Skills" value={profile.skills.length ? profile.skills.join(', ') : 'No skills added'} />
        </dl>

        <a className="profile-backlink" href="/login">
          Return to sign-in <ArrowUpRight size={15} />
        </a>
      </section>

      <footer className="profile-footer">Mongo App <span>·</span> Account information is private to your session.</footer>
    </main>
  )
}

function ProfileField({ label, value }: { label: string; value: string }) {
  return (
    <div className="profile-field">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  )
}