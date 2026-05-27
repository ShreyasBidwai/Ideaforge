import React from 'react';
import { Loader2, XSquare } from 'lucide-react';
import { motion } from 'framer-motion';

interface QueuePositionProps {
  position: number;
  estimatedWait: string;
  onCancel: () => void;
}

export const QueuePosition: React.FC<QueuePositionProps> = ({
  position,
  estimatedWait,
  onCancel,
}) => {
  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-6 text-center space-y-5 shadow-xl max-w-md mx-auto">
      <div className="space-y-1">
        <h3 className="text-zinc-400 text-xs font-semibold uppercase tracking-wider">Queue Position</h3>
        <p className="text-zinc-500 text-[11px]">Multiple builds queue sequentially to optimize agent subscription resource allocation.</p>
      </div>

      <div className="relative flex items-center justify-center py-4">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 8, ease: "linear" }}
          className="absolute w-32 h-32 border-2 border-dashed border-indigo-500/20 rounded-full"
        />
        <div className="relative bg-zinc-900 border border-zinc-800 w-24 h-24 rounded-full flex flex-col items-center justify-center shadow-lg">
          <span className="text-4xl font-extrabold text-white font-mono">{position}</span>
          <span className="text-[10px] text-zinc-400 font-bold uppercase -mt-0.5">IN QUEUE</span>
        </div>
      </div>

      <div className="bg-zinc-900/60 border border-zinc-850 p-4 rounded-lg space-y-2">
        <div className="flex items-center justify-center space-x-2 text-indigo-400 text-xs font-medium">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          <span>Waiting for previous builds to complete...</span>
        </div>
        <div className="text-xs text-zinc-300">
          Estimated Wait: <span className="font-semibold text-white">{estimatedWait}</span>
        </div>
      </div>

      <button
        onClick={onCancel}
        className="w-full flex items-center justify-center space-x-2 py-2 px-4 bg-zinc-900 hover:bg-zinc-850 active:bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white text-xs font-semibold rounded-lg transition-colors"
      >
        <XSquare className="w-4 h-4 text-zinc-400" />
        <span>Cancel & Leave Queue</span>
      </button>
    </div>
  );
};

export default QueuePosition;
