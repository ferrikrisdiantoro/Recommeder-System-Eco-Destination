import React, { useEffect, useState } from 'react'; import { api } from '../api'; import PlaceCard from '../components/PlaceCard'
export default function Bookmarks(){
  const [items,setItems]=useState([])
  const load=()=>api.get('/api/bookmarks').then(res=>setItems(res.data)).catch(console.error)
  useEffect(()=>{ load() },[])
  const del=async(p)=>{ if(!confirm('Hapus bookmark?')) return; try{ await api.delete(`/api/bookmarks/${p.place_id || p.id}`); load() }catch(e){ alert('Gagal hapus bookmark') } }
  return (<div><h1 className='text-xl font-semibold mb-4'>Bookmarks</h1><div className='grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4'>{items.map(p => (<div key={p.place_id} className='relative'><PlaceCard p={p} /><button onClick={()=>del(p)} className='absolute top-2 right-2 px-2 py-1 text-xs rounded bg-red-600 text-white'>Delete</button></div>))}</div></div>)
}
