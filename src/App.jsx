import { useState } from 'react'
import './App.css'
import Navbar from './component/navbar'
import LandManage from './component/LandManage'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>

      <Navbar />
      <LandManage />

    </>
  )
}

export default App
