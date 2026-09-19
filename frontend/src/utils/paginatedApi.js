const DEFAULT_PAGE_SIZE = 100

export const extractItems = (payload) => {
  if (Array.isArray(payload)) {
    return payload
  }

  if (payload && Array.isArray(payload.results)) {
    return payload.results
  }

  return []
}

export const isPaginatedPayload = (payload) =>
  Boolean(payload) &&
  !Array.isArray(payload) &&
  Array.isArray(payload.results) &&
  typeof payload.count !== 'undefined'

export const fetchAllPages = async (
  api,
  endpoint,
  { params = {}, pageSize = DEFAULT_PAGE_SIZE } = {}
) => {
  const firstResponse = await api.get(endpoint, {
    ...params,
    page: 1,
    page_size: pageSize,
  })

  const firstItems = extractItems(firstResponse)
  if (!isPaginatedPayload(firstResponse)) {
    return firstItems
  }

  const totalItems = Number(firstResponse.count || firstItems.length)
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize))

  if (totalPages === 1) {
    return firstItems
  }

  const remainingResponses = await Promise.all(
    Array.from({ length: totalPages - 1 }, (_, index) =>
      api.get(endpoint, {
        ...params,
        page: index + 2,
        page_size: pageSize,
      })
    )
  )

  return [firstItems, ...remainingResponses.map(extractItems)].flat()
}
