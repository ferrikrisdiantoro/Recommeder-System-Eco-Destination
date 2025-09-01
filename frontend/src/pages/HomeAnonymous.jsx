import React, { useEffect, useState } from 'react'
import { api } from '../api'; import PlaceCard from '../components/PlaceCard'
export default function HomeAnonymous(){
  const [items,setItems]=useState([])
  useEffect(()=>{ api.get('/api/recs/anonymous?k=12').then(res=>setItems(res.data)).catch(console.error) },[])
  return (<div><h1 className='text-xl font-semibold mb-4'>Rekomendasi Populer (untuk pengunjung anonim)</h1>
    <div className='grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4'>{items.map(p=><PlaceCard key={p.place_id} p={p} />)}</div></div>)
}
