import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '../contexts/AuthContext'

const schema = z.object({
  email: z.email('Введите корректный email'),
  password: z.string().min(8, 'Минимум 8 символов'),
  full_name: z.string().min(1, 'Введите имя'),
  business_name: z.string().min(1, 'Введите название компании'),
})

type FormData = z.infer<typeof schema>

const inputClass =
  'w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500'

export default function RegisterPage() {
  const { register: registerUser } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { email: '', password: '', full_name: '', business_name: '' },
  })

  const onSubmit = async (data: FormData) => {
    setError(null)
    try {
      await registerUser(data)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось зарегистрироваться')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex items-center justify-center gap-2">
          <div className="flex size-9 items-center justify-center rounded-lg bg-indigo-600 text-base font-bold text-white">
            F
          </div>
          <span className="text-xl font-semibold text-slate-900">FlowPilot</span>
        </div>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          <h1 className="text-lg font-semibold text-slate-900">Регистрация</h1>
          {error && (
            <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
          )}
          <div className="space-y-1">
            <label htmlFor="email" className="text-sm font-medium text-slate-700">
              Email
            </label>
            <input id="email" type="email" className={inputClass} {...register('email')} />
            {errors.email && <p className="text-xs text-red-600">{errors.email.message}</p>}
          </div>
          <div className="space-y-1">
            <label htmlFor="password" className="text-sm font-medium text-slate-700">
              Пароль
            </label>
            <input id="password" type="password" className={inputClass} {...register('password')} />
            {errors.password && <p className="text-xs text-red-600">{errors.password.message}</p>}
          </div>
          <div className="space-y-1">
            <label htmlFor="full_name" className="text-sm font-medium text-slate-700">
              Ваше имя
            </label>
            <input id="full_name" className={inputClass} {...register('full_name')} />
            {errors.full_name && (
              <p className="text-xs text-red-600">{errors.full_name.message}</p>
            )}
          </div>
          <div className="space-y-1">
            <label htmlFor="business_name" className="text-sm font-medium text-slate-700">
              Название компании
            </label>
            <input id="business_name" className={inputClass} {...register('business_name')} />
            {errors.business_name && (
              <p className="text-xs text-red-600">{errors.business_name.message}</p>
            )}
          </div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-60"
          >
            {isSubmitting ? 'Создаём аккаунт…' : 'Создать аккаунт'}
          </button>
          <p className="text-center text-sm text-slate-500">
            Уже есть аккаунт?{' '}
            <Link to="/login" className="font-medium text-indigo-600 hover:text-indigo-500">
              Войти
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}
