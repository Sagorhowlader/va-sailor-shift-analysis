// Vue app entry point: wires up the router and mounts the app shell defined
// in App.vue onto #app (see index.html). No other setup is needed -- every
// module fetches its own pre-computed JSON from /public/data on mount
// (see the onMounted() hook in each view under src/views/).
import { createApp } from 'vue'
import App from './App.vue'
import './style.css'
import router from './router'

createApp(App).use(router).mount('#app')
