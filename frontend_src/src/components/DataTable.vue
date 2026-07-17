<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  columns: { type: Array, required: true }, // [{key, label}]
  rows: { type: Array, required: true },
  // Optional cross-widget link: when true, rows become clickable and emit
  // row-click with the row's data -- lets a parent view wire a table to
  // another widget (e.g. clicking a Scoreboard row toggles that artist on
  // the Talent Radar chart) instead of the table being a dead end.
  clickable: { type: Boolean, default: false },
  isRowActive: { type: Function, default: () => false },
})
const emit = defineEmits(['row-click'])

const pageSize = ref(10)
const search = ref('')
const page = ref(1)
const sortKey = ref(null)
const sortAsc = ref(true)

// Parent components swap in a whole new (usually differently-sized) rows
// array whenever a filter changes (e.g. switching "Select Influence Genre").
// Without this, staying on page 4+ of the old data would show "no matching
// rows" against the new data until the user manually clicked back.
watch(
  () => props.rows,
  () => {
    page.value = 1
  }
)

const filtered = computed(() => {
  let out = props.rows
  if (search.value) {
    const q = search.value.toLowerCase()
    out = out.filter((r) => props.columns.some((c) => String(r[c.key] ?? '').toLowerCase().includes(q)))
  }
  if (sortKey.value) {
    out = [...out].sort((a, b) => {
      const av = a[sortKey.value]
      const bv = b[sortKey.value]
      if (av === bv) return 0
      const cmp = av > bv ? 1 : -1
      return sortAsc.value ? cmp : -cmp
    })
  }
  return out
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize.value)))

const paged = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filtered.value.slice(start, start + pageSize.value)
})

function sortBy(key) {
  if (sortKey.value === key) sortAsc.value = !sortAsc.value
  else {
    sortKey.value = key
    sortAsc.value = true
  }
}
</script>

<template>
  <div class="data-table">
    <div class="table-controls">
      <label>
        Show
        <select v-model.number="pageSize" @change="page = 1">
          <option :value="10">10</option>
          <option :value="25">25</option>
          <option :value="50">50</option>
        </select>
        entries
      </label>
      <label>
        Search:
        <input type="text" v-model="search" @input="page = 1" />
      </label>
    </div>

    <table>
      <thead>
        <tr>
          <th v-for="c in columns" :key="c.key" @click="sortBy(c.key)">
            {{ c.label }}
            <span v-if="sortKey === c.key">{{ sortAsc ? '▲' : '▼' }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, i) in paged"
          :key="i"
          :class="{ clickable, active: clickable && isRowActive(row) }"
          @click="clickable && emit('row-click', row)"
        >
          <td v-for="c in columns" :key="c.key">{{ row[c.key] }}</td>
        </tr>
        <tr v-if="!paged.length">
          <td :colspan="columns.length" class="empty">No matching rows</td>
        </tr>
      </tbody>
    </table>

    <div class="pagination">
      <span>{{ filtered.length }} entries</span>
      <div class="pager-buttons">
        <button :disabled="page <= 1" @click="page--">Prev</button>
        <span>Page {{ page }} / {{ totalPages }}</span>
        <button :disabled="page >= totalPages" @click="page++">Next</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.data-table {
  font-size: 0.78rem;
}
.table-controls {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  color: #555;
}
.table-controls input {
  border: 1px solid #ccd2d8;
  border-radius: 3px;
  padding: 0.2rem 0.4rem;
  margin-left: 0.3rem;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th {
  text-align: left;
  border-bottom: 2px solid #dfe3e6;
  padding: 0.4rem 0.5rem;
  cursor: pointer;
  color: #333;
  white-space: nowrap;
}
td {
  padding: 0.35rem 0.5rem;
  border-bottom: 1px solid #f0f0f0;
  color: #444;
}
.empty {
  text-align: center;
  color: #999;
  padding: 1rem;
}
tr.clickable {
  cursor: pointer;
}
tr.clickable:hover td {
  background: #f8fafc;
}
tr.active td {
  background: #e3f3ef;
  font-weight: 600;
}
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.5rem;
  color: #777;
}
.pager-buttons {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.pager-buttons button {
  border: 1px solid #ccd2d8;
  background: #fff;
  border-radius: 3px;
  padding: 0.15rem 0.5rem;
  cursor: pointer;
}
.pager-buttons button:disabled {
  opacity: 0.4;
  cursor: default;
}
</style>
