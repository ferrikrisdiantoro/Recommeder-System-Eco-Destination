import React, { useEffect, useState } from 'react'; import { useParams } from 'react-router-dom'; import { api } from '../api'; import RatingStars from '../components/RatingStars'
export default function Detail(){
  const { id } = useParams(); const [p,setP]=useState(null); const [comments,setComments]=useState([]); const [myRating,setMyRating]=useState(0); const [text,setText]=useState('')
  const load=()=>{ api.get(`/api/places/${id}`).then(res=>setP(res.data)).catch(console.error); api.get(`/api/comments?place_id=${id}`).then(res=>setComments(res.data)).catch(console.error) }
  useEffect(()=>{ load() },[id])
  const bookmark=async()=>{ try{ await api.post('/api/bookmarks',{place_id:Number(id)}); alert('Ditambahkan ke bookmark') }catch(e){ alert('Login dulu untuk bookmark.') } }
  const saveRating=async()=>{ if(!myRating){ alert('Pilih rating 1..5'); return } try{ await api.post('/api/ratings',{place_id:Number(id),rating:myRating}); alert('Rating disimpan') }catch(e){ alert('Login dulu untuk beri rating.') } }
  const sendComment=async()=>{ const t=text.trim(); if(!t) return; try{ await api.post('/api/comments',{place_id:Number(id),text:t}); setText(''); load() }catch(e){ alert('Login dulu untuk komentar.') } }
  if(!p) return <div>Loading...</div>
  return (<div className='max-w-4xl mx-auto'><div className='grid md:grid-cols-2 gap-4'><img src={p.image} className='w-full h-72 object-cover rounded-xl' /><div><h1 className='text-2xl font-semibold'>{p.place_name}</h1>
  <div className='text-gray-600'>{p.city} • {p.category}</div><div className='mt-2'>Harga: <b>{p.price || '-'}</b></div><div className='mt-1'>Rating: <b>{p.rating?.toFixed ? p.rating.toFixed(1) : p.rating}</b></div><div className='mt-2 text-gray-700'>{p.description}</div><div className='mt-2 text-gray-700'>Alamat: {p.address}</div><div className='mt-3 flex gap-2'><button onClick={bookmark} className='px-3 py-2 rounded bg-black text-white'>Bookmark</button>{p.map_url && <a href={p.map_url} target='_blank' className='px-3 py-2 rounded border'>Map</a>}</div></div></div>
  <div className='mt-6'><h2 className='font-semibold mb-2'>Galeri</h2><div className='grid grid-cols-3 gap-3'>{[p.gallery1,p.gallery2,p.gallery3].filter(Boolean).map((g,idx)=>(<img key={idx} src={g} className='w-full h-40 object-cover rounded-lg' />))}</div></div>
  <div className='mt-6'><h2 className='font-semibold mb-2'>Beri Rating</h2><RatingStars value={myRating} onChange={setMyRating} /><button onClick={saveRating} className='mt-2 px-3 py-1 rounded bg-black text-white'>Simpan</button></div>
  <div className='mt-6'><h2 className='font-semibold mb-2'>Komentar</h2><div className='flex gap-2'><input className='flex-1 border p-2 rounded' placeholder='Tulis komentar...' value={text} onChange={e=>setText(e.target.value)} /><button onClick={sendComment} className='px-3 py-1 rounded bg-black text-white'>Kirim</button></div>
  <div className='mt-3 space-y-2'>{comments.map(c=>(<div key={c.id} className='bg-white p-3 rounded border'><div className='text-sm text-gray-500'>{new Date(c.created_at).toLocaleString()}</div><div>{c.text}</div></div>))}</div></div></div>)
}
