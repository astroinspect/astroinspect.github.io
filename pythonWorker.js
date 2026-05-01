let pyodide

async function launchPyodide(reqs = undefined) {
  importScripts('https://cdn.jsdelivr.net/pyodide/v0.29.0/full/pyodide.js')

  self.postMessage({type: 'status', message: 'Loading pyodide'})

  pyodide = await loadPyodide()
  
  if (reqs?.length && reqs.length > 0) {
    self.postMessage({ type: 'status', message: 'Loading packages' })
    await pyodide.loadPackage(['micropip', ...reqs])
  }
}




async function loadPythonCode(script) {
  const resp = await fetch(script)
  const code = await resp?.text()
  if (!!code) {
    try {
      const r = await pyodide.runPythonAsync(code)
    } catch (e) {
      console.log('Code load error:', e)
    }
  }
}




async function evalFunction(func, args) {
  let result
  if (!!args) {
    pyodide.globals.set('kwargs', JSON.stringify(args))
    result = await pyodide.runPythonAsync(`exec_func(${func})`)
  } else {
    result = await pyodide.runPythonAsync(`${func}()`)
  }
  return result
}




self.onmessage = async function(e) {
  const { type, data } = e.data;
  
  switch (type) {
    case 'boot':
      try {
        await launchPyodide(data?.requirements)
        if (!!data?.script) {
          await loadPythonCode(data.script)
        }
        self.postMessage({ type: 'ready' })
      } catch (err) {
        self.postMessage({
          type: 'error',
          message: 'Falha ao carregar Pyodide',
          error: err.toString(),
        })
      }
      break
    case 'execute':
      if (!pyodide) {
        self.postMessage({
          type: 'error',
          message: 'Pyodide not initialized',
        })
        return
      }
      const result = await evalFunction(data?.func, data?.args)
      self.postMessage({
        type: 'result',
        data: result
      })
      break
  }
}


