import './ClusterCard.css';
import { Users } from 'lucide-react';
export default function ClusterCard({
    cluster,
    description,
}) {
    return (
        <div className="card flex flex-col gap-2 bg-[#17273b] h-full">
            <div className='flex gap-2 border-b border-[#0e1f31] p-3'>
                <Users color='#7882ad' size={24} />
                <h1 className="text-[#7882ad] font-semibold">PESONA MATCH</h1>
            </div>
            <h2 className="persona-name pl-3">
                {cluster}
            </h2>

            <p className="persona-description pl-3">
                {description}
            </p>
        </div>
    );
}