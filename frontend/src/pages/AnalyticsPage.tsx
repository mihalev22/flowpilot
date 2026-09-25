import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '../services/api'
import { SOURCE_LABELS } from '../components/badges'
import type { MessageSource } from '../services/api'
import { ErrorState, Skeleton, SkeletonCards } from '../components/states'

export default function AnalyticsPage() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['stats'],
    queryFn: dashboardApi.stats,
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-slate-900">Аналитика</h1>
        <SkeletonCards count={4} />
        <Skeleton className="h-64 rounded-xl" />
      </div>
    )
  }

  if (isError || !data) {
    return (
      <ErrorState
        message={error instanceof Error ? error.message : 'Не удалось загрузить аналитику'}
        onRetry={refetch}
      />
    )
  }

  const maxDay = Math.max(1, ...data.by_day.map((item) => item.count))
  const total = Math.max(1, data.total)
  const maxService = Math.max(1, ...data.top_services.map((item) => item.count))

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900">Аналитика</h1>

      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-semibold text-slate-900">Заявки за 14 дней</h2>
        <div className="mt-4 flex h-40 items-end gap-1">
          {data.by_day.map((day) => (
            <div
              key={day.date}
              className="flex-1 rounded-t bg-indigo-500/80 hover:bg-indigo-500"
              style={{ height: `${Math.max(4, (day.count / maxDay) * 100)}%` }}
              title={`${day.date}: ${day.count}`}
            >
              <div className="flex h-full items-start justify-center pt-1 text-[10px] text-indigo-100">
                {day.count > 0 ? day.count : ''}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-2 flex justify-between text-xs text-slate-400">
          <span>{data.by_day[0]?.date}</span>
          <span>{data.by_day[data.by_day.length - 1]?.date}</span>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold text-slate-900">Источники обращений</h2>
          {data.by_source.length === 0 ? (
            <p className="text-sm text-slate-500">Данных пока нет</p>
          ) : (
            data.by_source.map((source) => (
              <div key={source.source}>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-700">
                    {SOURCE_LABELS[source.source as MessageSource] ?? source.source}
                  </span>
                  <span className="text-slate-500">
                    {source.count} ({Math.round((source.count / total) * 100)}%)
                  </span>
                </div>
                <div className="mt-1 h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-blue-500"
                    style={{ width: `${(source.count / total) * 100}%` }}
                  />
                </div>
              </div>
            ))
          )}
        </div>

        <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold text-slate-900">Популярные услуги</h2>
          {data.top_services.length === 0 ? (
            <p className="text-sm text-slate-500">Данных пока нет</p>
          ) : (
            data.top_services.map((service) => (
              <div key={service.service_name}>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-700">{service.service_name}</span>
                  <span className="text-slate-500">{service.count}</span>
                </div>
                <div className="mt-1 h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-emerald-500"
                    style={{ width: `${(service.count / maxService) * 100}%` }}
                  />
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {(
          [
            ['Новые', data.status_counts.new, 'bg-blue-500'],
            ['В работе', data.status_counts.in_progress, 'bg-amber-500'],
            ['Подтверждено', data.status_counts.confirmed, 'bg-indigo-500'],
            ['Завершено', data.status_counts.completed, 'bg-emerald-500'],
            ['Отменено', data.status_counts.cancelled, 'bg-slate-400'],
          ] as const
        ).map(([label, value, color]) => (
          <div key={label} className="rounded-xl border border-slate-200 bg-white p-5">
            <p className="text-sm text-slate-500">{label}</p>
            <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100">
              <div
                className={color}
                style={{ width: `${(value / total) * 100}%`, height: '100%' }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
