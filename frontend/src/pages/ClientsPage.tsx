import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { clientsApi } from '../services/api'
import { formatDate } from '../components/badges'
import { EmptyState, ErrorState, Skeleton, SkeletonTable } from '../components/states'

export default function ClientsPage() {
  const [search, setSearch] = useState('')
  const [submittedSearch, setSubmittedSearch] = useState('')

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['clients', submittedSearch],
    queryFn: () => clientsApi.list(submittedSearch || undefined),
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900">Клиенты</h1>

      <form
        onSubmit={(event) => {
          event.preventDefault()
          setSubmittedSearch(search)
        }}
        className="flex max-w-md gap-2"
      >
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Поиск по имени или телефону"
          aria-label="Поиск клиентов"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        <button
          type="submit"
          className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
        >
          Найти
        </button>
      </form>

      {isFetching && <span className="text-xs text-slate-400">Обновление…</span>}

      {isLoading ? (
        <SkeletonTable rows={8} cols={4} />
      ) : isError ? (
        <ErrorState
          message={error instanceof Error ? error.message : 'Не удалось загрузить клиентов'}
          onRetry={refetch}
        />
      ) : !data || data.length === 0 ? (
        <EmptyState
          title="Клиентов не найдено"
          description="Клиенты создаются автоматически при обращениях через Telegram или веб-форму"
        />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3 font-medium">Имя</th>
                <th className="px-4 py-3 font-medium">Телефон</th>
                <th className="px-4 py-3 font-medium">Telegram</th>
                <th className="px-4 py-3 font-medium">Добавлен</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((client) => (
                <tr key={client.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <Link
                      to={`/clients/${client.id}`}
                      className="font-medium text-indigo-600 hover:text-indigo-500"
                    >
                      {client.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{client.phone ?? '—'}</td>
                  <td className="px-4 py-3 text-slate-600">
                    {client.telegram_user_id ? `ID ${client.telegram_user_id}` : '—'}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{formatDate(client.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {isLoading && <Skeleton className="h-4 w-24" />}
    </div>
  )
}
