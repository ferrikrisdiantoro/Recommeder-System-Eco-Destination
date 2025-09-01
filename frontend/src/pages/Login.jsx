import React, { useState } from 'react'; import { api, setAuthToken } from '../api'; import { useNavigate } from 'react-router-dom'
export default function Login(){
  const [email,setEmail]=useState(''),[password,setPassword]=useState(''),[err,setErr]=useState(''); const nav=useNavigate()
  const submit=async(e)=>{e.preventDefault();setErr('');try{const res=await api.post('/api/auth/login',{email,password});setAuthToken(res.data.token);nav('/home')}catch(e){setErr(e?.response?.data?.error||'Login gagal')}}
  return (<div className='max-w-md mx-auto'><h1 className='text-xl font-semibold mb-4'>Login</h1>
  <form onSubmit={submit} className='space-y-3'><input className='w-full border p-2 rounded' placeholder='Email' value={email} onChange={e=>setEmail(e.target.value)} />
  <input className='w-full border p-2 rounded' placeholder='Password' type='password' value={password} onChange={e=>setPassword(e.target.value)} />{err && <div className='text-red-600 text-sm'>{err}</div>}
  <button className='px-4 py-2 rounded bg-black text-white'>Masuk</button></form></div>)}
