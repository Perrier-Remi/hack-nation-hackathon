import { useCallback, useMemo } from 'react'
import ReactFlow, {
  Background,
  Controls,
  Edge,
  MarkerType,
  Node,
  NodeProps,
  Position,
} from 'reactflow'
import 'reactflow/dist/style.css'

export type PipelineStatus = 'idle' | 'running' | 'done' | 'error'

export type PipelineNodeId =
  | 'upload'
  | 'preprocess'
  | 'transcription'
  | 'safety'
  | 'llm'
  | 'veo'

export interface PipelineGraphProps {
  pipelineState: Record<PipelineNodeId, PipelineStatus>
  onTrigger: (nodeId: PipelineNodeId) => void
  disabled?: boolean
}

interface PipelineNodeData {
  id: PipelineNodeId
  label: string
  status: PipelineStatus
  onTrigger: (id: PipelineNodeId) => void
  disabled?: boolean
}

const statusColors: Record<PipelineStatus, string> = {
  idle: 'rgba(148, 163, 184, 0.25)',
  running: 'rgba(255, 176, 32, 0.2)',
  done: 'rgba(14, 159, 110, 0.2)',
  error: 'rgba(245, 101, 101, 0.2)',
}

const statusText: Record<PipelineStatus, string> = {
  idle: 'Waiting',
  running: 'Running…',
  done: 'Completed',
  error: 'Error',
}

const baseNodes: Array<Omit<Node<PipelineNodeData>, 'data'>> = [
  {
    id: 'upload',
    type: 'pipeline',
    position: { x: 0, y: 40 },
    sourcePosition: Position.Right,
  },
  {
    id: 'preprocess',
    type: 'pipeline',
    position: { x: 190, y: -10 },
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  },
  {
    id: 'transcription',
    type: 'pipeline',
    position: { x: 190, y: 180 },
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  },
  {
    id: 'safety',
    type: 'pipeline',
    position: { x: 380, y: -10 },
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  },
  {
    id: 'llm',
    type: 'pipeline',
    position: { x: 380, y: 180 },
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  },
  {
    id: 'veo',
    type: 'pipeline',
    position: { x: 580, y: 80 },
    targetPosition: Position.Left,
  },
]

const nodeLabels: Record<PipelineNodeId, string> = {
  upload: 'Upload',
  preprocess: 'Scene Detection',
  transcription: 'Transcription',
  safety: 'Safety Check',
  llm: 'LLM Summary',
  veo: 'Veo Enhancement',
}

const baseEdges: Edge[] = [
  { id: 'upload->preprocess', source: 'upload', target: 'preprocess' },
  { id: 'upload->transcription', source: 'upload', target: 'transcription' },
  { id: 'preprocess->safety', source: 'preprocess', target: 'safety' },
  { id: 'transcription->llm', source: 'transcription', target: 'llm' },
  { id: 'safety->veo', source: 'safety', target: 'veo' },
  { id: 'llm->veo', source: 'llm', target: 'veo' },
]

function PipelineNode({ data }: NodeProps<PipelineNodeData>) {
  const { id, label, status, onTrigger, disabled } = data
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
        borderRadius: 14,
        boxShadow: '0 18px 40px rgba(15, 23, 42, 0.12)',
        padding: '18px 22px',
        background: 'linear-gradient(135deg, #ffffff 0%, rgba(241, 245, 249, 0.95) 100%)',
        border: '1px solid rgba(148, 163, 184, 0.25)',
        color: 'var(--text-primary)',
        width: 170,
      }}
    >
      <span style={{ fontWeight: 600, fontSize: '1rem' }}>{label}</span>
      <span
        style={{
          fontSize: '0.75rem',
          padding: '4px 10px',
          borderRadius: 999,
          alignSelf: 'flex-start',
          background: statusColors[status],
          color: 'var(--text-secondary)',
        }}
      >
        {statusText[status]}
      </span>
      <button
        onClick={() => !disabled && onTrigger(id)}
        disabled={disabled}
        style={{
          marginTop: 6,
          padding: '8px 12px',
          fontSize: '0.8rem',
          borderRadius: 10,
          border: '1px solid rgba(99, 102, 241, 0.35)',
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(14, 165, 233, 0.15))',
          color: 'var(--text-primary)',
          cursor: disabled ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.55 : 1,
          transition: 'transform 0.2s ease, box-shadow 0.2s ease',
        }}
        onMouseEnter={(e) => {
          if (disabled) return
          ;(e.currentTarget.style.transform as any) = 'translateY(-2px)'
          e.currentTarget.style.boxShadow = '0 10px 25px rgba(99, 102, 241, 0.25)'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'none'
          e.currentTarget.style.boxShadow = 'none'
        }}
      >
        Trigger
      </button>
    </div>
  )
}

const nodeTypes = { pipeline: PipelineNode }

export function PipelineGraph({ pipelineState, onTrigger, disabled }: PipelineGraphProps) {
  const nodes = useMemo<Node<PipelineNodeData>[]>(
    () =>
      baseNodes.map((node) => ({
        ...node,
        data: {
          id: node.id as PipelineNodeId,
          label: nodeLabels[node.id as PipelineNodeId],
          status: pipelineState[node.id as PipelineNodeId] ?? 'idle',
          onTrigger,
          disabled,
        },
      })),
    [pipelineState, onTrigger, disabled]
  )

  const edges = useMemo<Edge[]>(
    () =>
      baseEdges.map((edge) => ({
        ...edge,
        style: { strokeWidth: 2, stroke: '#A0AEC0' },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#A0AEC0',
        },
        animated: pipelineState[edge.source as PipelineNodeId] === 'running',
      })),
    [pipelineState]
  )

  const handleNodeClick = useCallback(
    (_: unknown, node: Node) => {
      if (disabled) return
      onTrigger(node.id as PipelineNodeId)
    },
    [onTrigger, disabled]
  )

  return (
    <div
      style={{
        height: 520,
        width: '100%',
        background: 'var(--bg-darker)',
        borderRadius: 18,
        border: '1px solid rgba(148, 163, 184, 0.25)',
        boxShadow: '0 20px 45px rgba(15, 23, 42, 0.18)',
        overflow: 'hidden',
      }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        zoomOnScroll
        panOnDrag
        onNodeClick={handleNodeClick}
      >
        <Background color="rgba(148, 163, 184, 0.4)" gap={28} />
        <Controls />
      </ReactFlow>
    </div>
  )
}

export default PipelineGraph

