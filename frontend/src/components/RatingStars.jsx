import React from 'react'
export default function RatingStars({ value, onChange }){return (<div className='flex gap-1'>{[1,2,3,4,5].map(n=>(<button key={n} type='button' onClick={()=>onChange(n)} className={'w-7 h-7 rounded-full border flex items-center justify-center ' + (value>=n?'bg-yellow-400':'bg-white')}>{n}</button>))}</div>)}
