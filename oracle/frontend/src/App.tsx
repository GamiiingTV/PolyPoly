import { useOracleStore } from './hooks/useOracleStore'
import Dashboard from './components/Dashboard'

export default function App() {
  return <Dashboard {...useOracleStore()} />
}
