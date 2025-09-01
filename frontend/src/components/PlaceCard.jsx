import React from 'react'
import { Link } from 'react-router-dom'
export default function PlaceCard({ p, onBookmark }){
  return (<div className='bg-white rounded-xl shadow-sm p-3 flex flex-col'>
    <img src={p.image} alt={p.place_name} className='w-full h-44 object-cover rounded-lg' />
    <div className='mt-3 flex-1'>
      <h3 className='font-semibold'>{p.place_name}</h3>
      <div className='text-sm text-gray-500'>{p.city} • {p.category}</div>
      <div className='text-sm mt-1'>Harga: <span className='font-medium'>{p.price || '-'}</span></div>
      <div className='text-sm'>Rating: <span className='font-medium'>{(p.rating ?? 0).toFixed ? p.rating.toFixed(1) : p.rating}</span></div>
    </div>
    <div className='flex items-center gap-2 mt-3'>
      <Link to={`/place/${p.place_id || p.id}`} className='px-3 py-1 rounded-md bg-black text-white text-sm'>Detail</Link>
      {onBookmark && (<button onClick={()=>onBookmark(p)} className='px-3 py-1 rounded-md border text-sm'>Bookmark</button>)}
      {p.map_url && (<a href={p.map_url} target='_blank' className='px-3 py-1 rounded-md border text-sm'>Map</a>)}
    </div>
  </div>)
}
