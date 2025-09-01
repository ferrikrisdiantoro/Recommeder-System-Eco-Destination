import React, { useState } from 'react'; import { api, setAuthToken } from '../api'; import { useNavigate } from 'react-router-dom'
export default function Register(){
  const [name,setName]=useState(''),[email,setEmail]=useState(''),[password,setPassword]=useState(''),[err,setErr]=useState(''); const nav=useNavigate()
  const submit=async(e)=>{e.preventDefault();setErr('');try{const res=await api.post('/api/auth/register',{name,email,password});setAuthToken(res.data.token);nav('/onboarding')}catch(e){setErr(e?.response?.data?.error||'Register gagal')}}
  return (<div className='max-w-md mx-auto'><h1 className='text-xl font-semibold mb-4'>Register</h1>
  <form onSubmit={submit} className='space-y-3'><input className='w-full border p-2 rounded' placeholder='Nama' value={name} onChange={e=>setName(e.target.value)} />
  <input className='w-full border p-2 rounded' placeholder='Email' value={email} onChange={e=>setEmail(e.target.value)} />
  <input className='w-full border p-2 rounded' placeholder='Password' type='password' value={password} onChange={e=>setPassword(e.target.value)} />{err && <div className='text-red-600 text-sm'>{err}</div>}
  <button className='px-4 py-2 rounded bg-black text-white'>Daftar</button></form></div>)}
