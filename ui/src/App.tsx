import { useEffect } from 'react'
import './App.css'
import WorkflowPage from './components/WorkflowPage'

const App = () => {
  // Load Bootstrap Icons from CDN
  useEffect(() => {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css'
    document.head.appendChild(link)

    return () => {
      document.head.removeChild(link)
    }
  }, [])

  return <WorkflowPage />
}

export default App
