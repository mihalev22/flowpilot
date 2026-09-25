import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { clientsApi, requestsApi } from '../services/api'
import type { RequestStatus } from '../services/api'
import { useToast } from '../contexts/ToastContext'
import { formatDateTime, IntentBadge, SOURCE_LABELS, STATUS_LABELS, StatusBadge } from '../components/badges'
import { EmptyState, ErrorState, Skeleton, SkeletonTable } from '../components/states'

const PAGE_SIZE = 20

const createSchema = z.object({
  client_id: z.number({ message: 'Выберите клиента' }).int().positive(),
  text: z.string().min(1, 'Введите текст обращения').max(4000, 'Максимум 4000 символов'),
})

type CreateFormData = z.infer<typeof createSchema>

const selectClass =
  'rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500'

export default function RequestsPage() {
  const [status, setStatus] = useState<RequestStatus | ''>('')
  const [reviewOnly, setReviewOnly] = useState(false)
  const [page, setPage] = useState(0)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const { show } = useToast()
  const queryClient = useQueryClient()

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['requests', status, reviewOnly, page],
    queryFn: () =>
      requestsApi.list({
        status: status || undefined,
        requires_review: reviewOnly ? true : undefined,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      }),
  })

  const { data: clients } = useQuery({
    queryKey: ['clients', ''],
    queryFn: () => clientsApi.list(),
    enabled: showCreateForm,
  })

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateFormData>({
    resolver: zodResolver(createSchema),
    defaultValues: { client_id: 0, text: '' },
  })

  const createMutation = useMutation({
    mutationFn: requestsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requests'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      setShowCreateForm(false)
      reset()
      show('Заявка создана', 'success')
    },
    onError: (err) => {
      show(err instanceof Error ? err.message : 'Не удалось создать заявку', 'error')
    },
  })

  const onCreateSubmit = (data: CreateFormData) => {
    createMutation.mutate(data)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-900">Заявки</h1>
        <button
          type="button"
          onClick={() => setShowCreateForm((value) => !value)}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          {showCreateForm ? 'Отмена' : 'Новая заявка'}
        </button>
      </div>

      {showCreateForm && (
        <form
          onSubmit={handleSubmit(onCreateSubmit)}
          className="space-y-4 rounded-xl border border-slate-200 bg-white p-5"
        >
          <h2 className="text-sm font-semibold text-slate-900">Новая заявка</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1">
              <label htmlFor="client_id" className="text-sm font-medium text-slate-700">
                Клиент
              </label>
              <select id="client_id" className={`${selectClass} w-full`} {...register('client_id')}>
                <option value={0}>Выберите клиента</option>
                {clients?.map((client) => (
                  <option key={client.id} value={client.id}>
                    {client.name}
                    {client.phone ? ` — ${client.phone}` : ''}
                  </option>
                ))}
              </select>
              {errors.client_id && (
                <p className="text-xs text-red-600">{errors.client_id.message}</p>
              )}
            </div>
            <div className="space-y-1">
              <label htmlFor="text" className="text-sm font-medium text-slate-700">
                Текст обращения
              </label>
              <textarea
                id="text"
                rows={3}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                placeholder="Например: хочу записаться на стрижку завтра в 15:00"
                {...register('text')}
              />
              {errors.text && <p className="text-xs text-red-600">{errors.text.message}</p>}
            </div>
          </div>
          <button
            type="submit"
            disabled={createMutation.isPending || isSubmitting}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-60"
          >
            {createMutation.isPending ? 'Создаём…' : 'Создать заявку'}
          </button>
        </form>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <select
          aria-label="Фильтр по статусу"
          value={status}
          onChange={(event) => {
            setStatus(event.target.value as RequestStatus | '')
            setPage(0)
          }}
          className={selectClass}
        >
          <option value="">Все статусы</option>
          {(Object.keys(STATUS_LABELS) as RequestStatus[]).map((value) => (
            <option key={value} value={value}>
              {STATUS_LABELS[value]}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={reviewOnly}
            onChange={(event) => {
              setReviewOnly(event.target.checked)
              setPage(0)
            }}
            className="size-4 rounded border-slate-300"
          />
          Только требующие проверки
        </label>
        {isFetching && <span className="text-xs text-slate-400">Обновление…</span>}
      </div>

      {isLoading ? (
        <SkeletonTable rows={8} cols={6} />
      ) : isError ? (
        <ErrorState
          message={error instanceof Error ? error.message : 'Не удалось загрузить заявки'}
          onRetry={refetch}
        />
      ) : !data || data.length === 0 ? (
        <EmptyState
          title="Заявок нет"
          description="Измените фильтры или создайте заявку вручную"
        />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3 font-medium">№</th>
                <th className="px-4 py-3 font-medium">Клиент</th>
                <th className="px-4 py-3 font-medium">Услуга</th>
                <th className="px-4 py-3 font-medium">AI</th>
                <th className="px-4 py-3 font-medium">Источник</th>
                <th className="px-4 py-3 font-medium">Дата</th>
                <th className="px-4 py-3 font-medium">Статус</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((request) => (
                <tr key={request.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <Link to={`/requests/${request.id}`} className="font-medium text-indigo-600">
                      {request.id}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-900">
                    <Link to={`/clients/${request.client_id}`} className="hover:underline">
                      {request.client?.name ?? `Клиент №${request.client_id}`}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{request.service_name ?? '—'}</td>
                  <td className="px-4 py-3">
                    <span className="flex items-center gap-2">
                      {request.latest_ai && <IntentBadge intent={request.latest_ai.intent} />}
                      {request.requires_manual_review && (
                        <span className="inline-flex items-center rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-200">
                          Проверка
                        </span>
                      )}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {SOURCE_LABELS[request.source]}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {formatDateTime(request.created_at)}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={request.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex items-center justify-between">
        <button
          type="button"
          disabled={page === 0}
          onClick={() => setPage((value) => Math.max(0, value - 1))}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
        >
          Назад
        </button>
        <span className="text-sm text-slate-500">Страница {page + 1}</span>
        <button
          type="button"
          disabled={!data || data.length < PAGE_SIZE}
          onClick={() => setPage((value) => value + 1)}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
        >
          Вперёд
        </button>
      </div>

      {isLoading && <Skeleton className="h-4 w-24" />}
    </div>
  )
}
