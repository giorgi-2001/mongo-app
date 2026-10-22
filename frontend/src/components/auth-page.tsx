import { useState, type ComponentProps, type ReactNode } from 'react'
import { Link, useNavigate } from '@tanstack/react-router'
import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowRight, Database, Eye, EyeOff, LoaderCircle } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { loginUser, registerUser } from '../lib/auth-api'

const loginSchema = z.object({
  email: z.email('Enter a valid email address.'),
  password: z.string().min(1, 'Enter your password.'),
})

const registerSchema = z.object({
  email: z.email('Enter a valid email address.'),
  age: z.number().int('Enter your age as a whole number.').min(13, 'You must be at least 13.').max(120, 'Enter a valid age.'),
  password: z.string().min(8, 'Use at least 8 characters.'),
  confirmPassword: z.string(),
}).refine((values) => values.password === values.confirmPassword, {
  message: 'Passwords do not match.',
  path: ['confirmPassword'],
})

type AuthPageProps = { mode: 'login' | 'register' }
type LoginValues = z.infer<typeof loginSchema>
type RegisterValues = z.infer<typeof registerSchema>

function getErrorMessage(error: unknown) {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = error.response
    if (typeof response === 'object' && response !== null && 'data' in response) {
      const data = response.data
      if (typeof data === 'object' && data !== null && 'detail' in data) {
        const detail = data.detail
        if (typeof detail === 'string') return detail
      }
    }
  }
  return 'We could not complete that request. Check your connection and try again.'
}

export function AuthPage({ mode }: AuthPageProps) {
  const isRegister = mode === 'register'
  const navigate = useNavigate()
  const [passwordVisible, setPasswordVisible] = useState(false)
  const [formMessage, setFormMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null)
  const loginForm = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })
  const registerForm = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: '', age: 18, password: '', confirmPassword: '' },
  })

  async function submitLogin(values: LoginValues) {
    setFormMessage(null)
    try {
      await loginUser(values.email, values.password)
      await navigate({ to: '/profile' })
    } catch (error) {
      setFormMessage({ type: 'error', text: getErrorMessage(error) })
    }
  }

  async function submitRegistration(values: RegisterValues) {
    setFormMessage(null)
    try {
      await registerUser({ email: values.email, age: values.age, password: values.password })
      setFormMessage({ type: 'success', text: 'Account created. Sign in to continue.' })
      window.setTimeout(() => void navigate({ to: '/login' }), 900)
    } catch (error) {
      setFormMessage({ type: 'error', text: getErrorMessage(error) })
    }
  }

  const errors = isRegister ? registerForm.formState.errors : loginForm.formState.errors
  const isSubmitting = isRegister ? registerForm.formState.isSubmitting : loginForm.formState.isSubmitting

  return (
    <main className="auth-page">
      <aside className="brand-panel">
        <Link to="/login" className="brand-lockup" aria-label="Mongo App home">
          <span className="brand-mark"><Database size={19} strokeWidth={2.2} /></span>
          <span>Mongo App</span>
        </Link>

        <div className="brand-copy">
          <p className="brand-eyebrow">A workspace for what matters</p>
          <h1>Your Mongo workspace starts here.</h1>
          <p>Sign in to pick up where you left off, or create an account to get started.</p>
        </div>

        <div className="brand-graphic" aria-hidden="true">
          <div className="data-row"><span /><span>users</span><span>collection</span></div>
          <div className="data-row"><span /><span>documents</span><span>organized</span></div>
          <div className="data-row"><span /><span>workspace</span><span>ready</span></div>
        </div>
        <div className="brand-footer">Mongo App <span>·</span> Your data, in good company.</div>
      </aside>

      <section className="form-panel" aria-labelledby="form-heading">
        <div className="auth-form-wrap">
          <p className="form-eyebrow">{isRegister ? 'Create your account' : 'Welcome back'}</p>
          <h2 id="form-heading">{isRegister ? 'Get started' : 'Sign in to Mongo App'}</h2>
          <p className="form-intro">
            {isRegister ? 'A few details and your workspace is ready.' : 'Enter your details to access your workspace.'}
          </p>

          {formMessage && (
            <p className={`form-alert ${formMessage.type}`} role="status">{formMessage.text}</p>
          )}

          <Button
            className="google-auth-button"
            variant="outline"
            type="button"
            onClick={() => {
              const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? '/api/v1').replace(/\/+$/, '')
              window.location.assign(`${apiBaseUrl}/auth/oidc/google/login`)
            }}
          >
            <GoogleMark />
            <span>Continue with Google</span>
          </Button>
          <div className="auth-divider"><span>or continue with email</span></div>

          {isRegister ? (
            <form className="auth-form" onSubmit={registerForm.handleSubmit(submitRegistration)} noValidate>
              <Field label="Email address" error={errors.email?.message}>
                <Input id="email-address" className="auth-input" type="email" autoComplete="email" placeholder="you@example.com" {...registerForm.register('email')} />
              </Field>
              <Field label="Age" error={registerForm.formState.errors.age?.message}>
                <Input id="age" className="auth-input" type="number" min="13" max="120" autoComplete="off" {...registerForm.register('age', { valueAsNumber: true })} />
              </Field>
              <Field label="Password" error={registerForm.formState.errors.password?.message}>
                <PasswordInput id="password" visible={passwordVisible} onToggle={() => setPasswordVisible(!passwordVisible)} autoComplete="new-password" placeholder="At least 8 characters" {...registerForm.register('password')} />
              </Field>
              <Field label="Confirm password" error={registerForm.formState.errors.confirmPassword?.message}>
                <PasswordInput id="confirm-password" visible={passwordVisible} onToggle={() => setPasswordVisible(!passwordVisible)} autoComplete="new-password" placeholder="Enter your password again" {...registerForm.register('confirmPassword')} />
              </Field>
              <SubmitButton isSubmitting={isSubmitting} label="Create account" />
            </form>
          ) : (
            <form className="auth-form" onSubmit={loginForm.handleSubmit(submitLogin)} noValidate>
              <Field label="Email address" error={errors.email?.message}>
                <Input id="email-address" className="auth-input" type="email" autoComplete="email" placeholder="you@example.com" {...loginForm.register('email')} />
              </Field>
              <Field label="Password" error={errors.password?.message}>
                <PasswordInput id="password" visible={passwordVisible} onToggle={() => setPasswordVisible(!passwordVisible)} autoComplete="current-password" placeholder="Enter your password" {...loginForm.register('password')} />
              </Field>
              <SubmitButton isSubmitting={isSubmitting} label="Sign in" />
            </form>
          )}

          <p className="auth-switch">
            {isRegister ? 'Already have an account? ' : 'New to Mongo App? '}
            <Link to={isRegister ? '/login' : '/register'}>{isRegister ? 'Sign in' : 'Create an account'}</Link>
          </p>
          <p className="auth-footnote">By continuing, you agree to use Mongo App responsibly.</p>
        </div>
      </section>
    </main>
  )
}

function GoogleMark() {
  return (
    <svg aria-hidden="true" viewBox="0 0 48 48" width="18" height="18">
      <path fill="#4285F4" d="M43.6 24.5c0-1.4-.1-2.8-.4-4.1H24v7.8h11a9.4 9.4 0 0 1-4.1 6.2v5.1h6.6c3.9-3.6 6.1-8.8 6.1-15Z" />
      <path fill="#34A853" d="M24 44c5.5 0 10.1-1.8 13.5-4.9l-6.6-5.1c-1.8 1.2-4.1 2-6.9 2-5.3 0-9.8-3.6-11.4-8.4H5.8V33A20 20 0 0 0 24 44Z" />
      <path fill="#FBBC05" d="M12.6 27.6a12 12 0 0 1 0-7.2v-5.4H5.8a20 20 0 0 0 0 18l6.8-5.4Z" />
      <path fill="#EA4335" d="M24 12c3 0 5.7 1 7.8 3.1l5.8-5.8A19.4 19.4 0 0 0 24 4 20 20 0 0 0 5.8 15l6.8 5.4C14.2 15.6 18.7 12 24 12Z" />
    </svg>
  )
}

function Field({ label, error, children }: { label: string; error?: string; children: ReactNode }) {
  const id = label.toLowerCase().replace(/ /g, '-')
  return (
    <div className="field-group">
      <label htmlFor={id}>{label}</label>
      {children}
      {error && <p className="field-error" role="alert">{error}</p>}
    </div>
  )
}

function PasswordInput({ visible, onToggle, ...props }: ComponentProps<typeof Input> & { visible: boolean; onToggle: () => void }) {
  return (
    <div className="password-control">
      <Input className="auth-input" type={visible ? 'text' : 'password'} {...props} />
      <button className="password-toggle" type="button" onClick={onToggle} aria-label={visible ? 'Hide password' : 'Show password'}>
        {visible ? <EyeOff size={16} /> : <Eye size={16} />}
      </button>
    </div>
  )
}

function SubmitButton({ isSubmitting, label }: { isSubmitting: boolean; label: string }) {
  return (
    <Button className="auth-submit" type="submit" disabled={isSubmitting}>
      <span>{isSubmitting ? 'Please wait...' : label}</span>
      {isSubmitting ? <LoaderCircle className="animate-spin" size={16} /> : <ArrowRight size={16} />}
    </Button>
  )
}