import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

type NavItem = {
  to: string
  label: string
  adminOnly?: boolean
  end?: boolean
}

const NAV: NavItem[] = [
  { to: '/', label: 'Дашборд', end: true },
  { to: '/requests', label: 'Заявки' },
  { to: '/clients', label: 'Клиенты' },
  { to: '/analytics', label: 'Аналитика', adminOnly: true },
  { to: '/settings', label: 'Настройки', adminOnly: true },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const items = NAV.filter((item) => !item.adminOnly || user?.role === 'admin')

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `block rounded-lg px-3 py-2 text-sm font-medium ${
      isActive ? 'bg-slate-100 text-slate-900' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
    }`

  return (
    <div className="min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 hidden w-60 flex-col border-r border-slate-200 bg-white md:flex">
        <div className="flex items-center gap-2 border-b border-slate-200 px-6 py-5">
          <div className="flex size-8 items-center justify-center rounded-lg bg-indigo-600 text-sm font-bold text-white">
            F
          </div>
          <span className="text-lg font-semibold text-slate-900">FlowPilot</span>
        </div>
        <nav className="flex-1 space-y-1 px-3 py-4">
          {items.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={navLinkClass}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-slate-200 px-3 py-4">
          <div className="px-3 pb-2">
            <p className="truncate text-sm font-medium text-slate-900">{user?.full_name}</p>
            <p className="text-xs text-slate-500">
              {user?.role === 'admin' ? 'Администратор' : 'Менеджер'}
            </p>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900"
          >
            Выйти
          </button>
        </div>
      </aside>

      <div className="md:pl-60">
        <nav className="flex gap-1 overflow-x-auto border-b border-slate-200 bg-white px-4 py-2 md:hidden">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `whitespace-nowrap rounded-lg px-3 py-1.5 text-sm font-medium ${
                  isActive ? 'bg-slate-100 text-slate-900' : 'text-slate-600'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
          <button
            type="button"
            onClick={handleLogout}
            className="ml-auto whitespace-nowrap rounded-lg px-3 py-1.5 text-sm font-medium text-slate-600"
          >
            Выйти
          </button>
        </nav>
        <main className="mx-auto max-w-6xl p-4 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
