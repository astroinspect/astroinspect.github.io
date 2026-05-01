class Semaphore {
  /**
   * Creates a semaphore that limits the number of concurrent Promises being handled
   * @param {*} maxConcurrentRequests max number of concurrent promises being handled at any time
   */
  constructor(maxConcurrentRequests = 1) {
    this.currentRequests = []
    this.runningRequests = 0
    this.maxConcurrentRequests = maxConcurrentRequests
  }

  /**
   * Returns a Promise that will eventually return the result of the function passed in
   * Use this to limit the number of concurrent function executions
   * @param {*} fnToCall function that has a cap on the number of concurrent executions
   * @param  {...any} args any arguments to be passed to fnToCall
   * @returns Promise that will resolve with the resolved value as if the function passed in was directly called
   */
  callFunction(fnToCall, ...args) {
    return new Promise((resolve, reject) => {
      this.currentRequests.push({
        resolve,
        reject,
        fnToCall,
        args,
      })
      this.tryNext()
    })
  }

  tryNext() {
    if (this.runningRequests < this.maxConcurrentRequests) {
      const curr = this.currentRequests.shift()
      if (curr) {
        this.runningRequests++
        const args = curr.args
        let req = curr.fnToCall.apply(null, args)
        req.then((res) => curr.resolve(res))
          .catch((err) => curr.reject(err))
          .finally(() => {
            this.runningRequests--
            this.tryNext()
          })
      }

    }
  }
}

class SemaphorePool {
  constructor() {
    this.pool = {}
    this.controller = new AbortController()
  }

  create(id, maxConcurrency) {
    if (!(id in this.pool)) {
      this.pool[id] = new Semaphore(maxConcurrency)
    }
  }

  enqueue(id, factory, ...args) {
    return this.pool[id].callFunction(factory, ...args)
  }

  getSignal() {
    return this.controller.signal
  }

  clear() {
    this.controller.abort()
    this.controller = new AbortController()
  }
}

const sleep = (time) => new Promise((resolve, reject) => {
  setTimeout(() => resolve(), time)
})

const sp = new SemaphorePool()
sp.create('legacy-rgb', 1)
sp.create('legacy-rgb-proxy', 1)
sp.create('splus-trilogy', 2)
sp.create('splus-lupton', 2)
sp.create('splus-photospec', 2)

const urlMap = [
  { url: 'https://www.legacysurvey.org/viewer/cutout.jpg', key: 'legacy-rgb' },
  { url: 'https://checker-melted-forsythia.glitch.me/legacy.jpg', key: 'legacy-rgb-proxy' },
  { url: 'https://checker-melted-forsythia.glitch.me/trilogy.png', key: 'splus-trilogy' },
  { url: 'https://checker-melted-forsythia.glitch.me/lupton.png', key: 'splus-lupton' },
  { url: 'https://astrotools.vercel.app/plot', key: 'splus-photospec' }
]


self.addEventListener('install', function (event) {
  self.skipWaiting()
  console.log('Service Worker installed')
})

self.addEventListener('fetch', function (event) {
  const url = event.request.url
  for (const uk of urlMap) {
    if (url.startsWith(uk.url)) {
      event.respondWith(
        sp.enqueue(uk.key, async () => {
          let attempt = 0
          let sleepTime = 500
          let resp
          do {
            if (url.startsWith(urlMap[0].url)) await sleep(sleepTime)
            resp = await fetch(event.request, { signal: sp.getSignal() })
            attempt++
            sleepTime += 250
          } while (resp.status == 429 && attempt <= 3)
          return resp
        })
      )
      break
    }
  }
})