import React, { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { initAuthFromStorage } from './api'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import HomeAnonymous from './pages/HomeAnonymous'
import HomeAuth from './pages/HomeAuth'
import Login from './pages/Login'
import Register from './pages/Register'
import About from './pages/About'
import Contact from './pages/Contact'
import Detail from './pages/Detail'
import Bookmarks from './pages/Bookmarks'
import Onboarding from './pages/Onboarding'
function Protected({ children }){ const token=localStorage.getItem('token'); return token ? children : <Navigate to='/login' replace /> }
export default function App(){
  useEffect(()=>{ initAuthFromStorage() },[])
  return (<div className='min-h-screen flex flex-col'>
    <Navbar /><main className='flex-1 container mx-auto px-4 py-6'>
      <Routes>
        <Route path='/' element={<HomeAnonymous />} />
        <Route path='/login' element={<Login />} />
        <Route path='/register' element={<Register />} />
        <Route path='/about' element={<About />} />
        <Route path='/contact' element={<Contact />} />
        <Route path='/place/:id' element={<Detail />} />
        <Route path='/bookmarks' element={<Protected><Bookmarks /></Protected>} />
        <Route path='/onboarding' element={<Protected><Onboarding /></Protected>} />
        <Route path='/home' element={<Protected><HomeAuth /></Protected>} />
        <Route path='*' element={<Navigate to='/' replace />} />
      </Routes>
    </main><Footer /></div>)
}
