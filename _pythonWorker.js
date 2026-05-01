'use client'

self.onmessage = async (event) => {
  const {type, data} = event.data

  if (type == 'exec') {
    const {func, args} = data
    console.log(`Executing function ${func} with args ${args}`)
    await new Promise((resolve) => setTimeout(resolve, 3000))
    self.postMessage({
      type: 'result',
      data: 'ok'
    })
  }
}

// import { loadPyodide } from 'pyodide'

// let pyodide = null

// // Função para carregar Pyodide
// async function launchPyodide() {
//   self.postMessage({ type: 'status', message: 'Importando Pyodide...' })
  
//   self.postMessage({ type: 'status', message: 'Inicializando Pyodide...' })
  
//   pyodide = await loadPyodide({
//       indexURL: "https://cdn.jsdelivr.net/pyodide/v0.23.4/full/"
//   })

//   self.postMessage({ type: 'status', message: 'Carregando pacotes...' })
  
//   // Carrega os pacotes necessários
//   await pyodide.loadPackage(["micropip", "numpy", "matplotlib"])

//   self.postMessage({ type: 'status', message: 'Configurando matplotlib...' })
  
//   // Configura matplotlib para funcionar em headless mode
//   await pyodide.runPythonAsync(`
// import matplotlib
// matplotlib.use('Agg')
// import matplotlib.pyplot as plt
// import numpy as np
// import base64
// from io import BytesIO
// import time
//   `)
// }


// async function generatePlot() {
//   try {
//     const pythonCode = `
// time.sleep(1)
// v = "Hello"
// v`

//   const result = await pyodide.runPythonAsync(pythonCode);
  
//   self.postMessage({
//     type: 'result',
//     result: result,
//   });

//   } catch (error) {
//     self.postMessage({
//       type: 'error',
//       message: 'Erro ao gerar plot',
//       error: error.toString()
//     });
//   }
// }


// self.onmessage = async function(e) {
//   const data = e.data;
  
//   switch (data.type) {
//     case 'init':
//       await loadPyodide()
//       break
        
//     case 'execute':
//       if (!pyodide) {
//         self.postMessage({
//           type: 'error',
//           message: 'Pyodide não inicializado'
//         })
//         return
//       }
//       await generatePlot()
//       break
//   }
// }


// launchPyodide().then(() => {
//   self.postMessage({ type: 'ready' })
// }).catch(error => {
//   self.postMessage({
//     type: 'error',
//     message: 'Falha ao carregar Pyodide',
//     error: error.toString()
//   })
// })