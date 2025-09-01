import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { setAuthToken } from '../api'
export default function Navbar(){
  const token=localStorage.getItem('token'); const nav=useNavigate()
  const logout=()=>{ setAuthToken(null); nav('/') }
  return (<nav className='bg-white border-b'>
    <div className='container mx-auto px-4 py-3 flex items-center justify-between'>
      <div className='flex items-center gap-4'>
        <Link to='/' className='font-semibold text-lg'>EcoTourism</Link>
        <Link to='/about' className='text-gray-600 hover:text-gray-900'>About</Link>
        <Link to='/contact' className='text-gray-600 hover:text-gray-900'>Contact</Link>
        {token && (<>
          <Link to='/home' className='text-gray-600 hover:text-gray-900'>Home (AI)</Link>
          <Link to='/bookmarks' className='text-gray-600 hover:text-gray-900'>Bookmarks</Link>
          <Link to='/onboarding' className='text-gray-600 hover:text-gray-900'>Rate</Link>
        </>)}
      </div>
      <div>{!token ? (<div className='flex items-center gap-3'>
        <Link to='/login' className='px-3 py-1 rounded-md border'>Login</Link>
        <Link to='/register' className='px-3 py-1 rounded-md bg-black text-white'>Register</Link>
      </div>) : (<button onClick={logout} className='px-3 py-1 rounded-md bg-red-600 text-white'>Logout</button>)}</div>
    </div>
  </nav>)
}
