import React, { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network';

export default function NetworkGraph({
  networkData,
  targetLemma,
  targetFormId,
  width = '250px',
  height = '200px',
}) {
  const containerRef = useRef(null);
  const modalContainerRef = useRef(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const displayFormId = targetFormId || 'N/A';
  
  // Helper to initialize the vis.js network
  const initNetwork = (container, data, optionsOverrides = {}) => {
    if (!container || !data) return null;

    const visNodes = data.nodes.map(([nodeId, freq]) => {
      const label = nodeId.replace(/_.*/g, ''); // Strip suffixes
      const isTarget = label === targetLemma;
      return {
        id: nodeId,
        value: freq,
        label: label,
        color: isTarget ? "#ec325d" : undefined,
        border: isTarget ? "red" : undefined
      };
    });

    const sourceCount = {};
    const visEdges = data.edges.map(([src, tgt, freq]) => {
      if (!sourceCount[src]) sourceCount[src] = 0;
      let roundVal = 0.2 * sourceCount[src];
      if (roundVal > 1) roundVal = 1.0;
      sourceCount[src]++;

      return {
        from: src,
        to: tgt,
        value: freq,
        arrows: "to",
        color: "#08c",
        smooth: {
          type: 'curvedCW',
          roundness: roundVal,
          forceDirection: "none"
        }
      };
    });

    const options = {
      layout: {
        hierarchical: { direction: "LR", sortMethod: "directed" }
      },
      physics: true,
      nodes: {
        shape: "dot",
        font: { size: 25, face: 'antinoouRegular, sans-serif' },
        scaling: {
          customScalingFunction: (min, max, total, value) => value / total,
          min: 5,
          max: 150
        }
      },
      interaction: {
        dragNodes: true,
        dragView: true,
        zoomView: true
      },
      ...optionsOverrides
    };
    return new Network(container, { nodes: visNodes, edges: visEdges }, options);
  };

  // Effect for Thumbnail
  useEffect(() => {
    if (isExpanded) return; // Don't render thumb canvas if modal is open
    const network = initNetwork(containerRef.current, networkData, {
      interaction: { dragNodes: false, dragView: false, zoomView: false } // Disable interaction on thumb
    });
    return () => { if (network) network.destroy(); };
  }, [networkData, targetLemma, isExpanded]);

  // Effect for Modal
  useEffect(() => {
    if (!isExpanded) return;
    const network = initNetwork(modalContainerRef.current, networkData);
    return () => { if (network) network.destroy(); };
  }, [networkData, targetLemma, isExpanded]);

  return (
    <>
      {/* Thumbnail */}
      <div 
        ref={containerRef} 
        onClick={() => setIsExpanded(true)}
        title="Click to expand phrase network"
        style={{ width, height, backgroundColor: '#fdfdfd', border: '1px solid black', cursor: 'pointer', position: 'relative' }}
      >
        <div style={{ position: 'absolute', bottom: '5px', right: '5px', fontSize: '0.8em', color: '#888', zIndex: 10 }}>
          <i className="fa fa-expand"></i> Expand
        </div>
      </div>

      {/* Full Screen Modal */}
      {isExpanded && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.8)', zIndex: 9999,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'
        }}>
          <div style={{ width: '90vw', height: '90vh', backgroundColor: '#fff', borderRadius: '8px', position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <div style={{ flex: '0 0 auto', padding: '14px 20px 10px 20px', borderBottom: '1px solid #e3e3e3', position: 'relative' }}>
              <button
                onClick={() => setIsExpanded(false)}
                style={{ position: 'absolute', top: '14px', right: '20px', zIndex: 100, padding: '5px 15px', cursor: 'pointer' }}
                className="btn btn-danger"
              >
                Close
              </button>
              <h4 style={{ margin: 0, paddingRight: '100px' }}>
                Term network for TLA form no. {displayFormId}: <span style={{ fontFamily: 'antinoouRegular' }}>{targetLemma}</span>
              </h4>
              <div style={{ marginTop: '4px', color: '#555', fontSize: '0.95em' }}>
                (scroll/pinch to zoom, click &amp; drag to pan)
              </div>
            </div>

            <div style={{ flex: '1 1 auto', minHeight: 0 }}>
              <div ref={modalContainerRef} style={{ width: '100%', height: '100%', outline: 'none' }} />
            </div>

            <div style={{ flex: '0 0 auto', padding: '10px 16px', borderTop: '1px solid #e3e3e3', backgroundColor: '#f9f9f9', fontSize: '0.9em', lineHeight: 1.35 }}>
              This term network shows a diagram of up to 20 most common phrases headed by <span style={{ fontFamily: 'antinoouRegular' }}>{targetLemma}</span>, truncated to 8 words at most for readability. Nodes and transitions are sized proportionally to how often they are attested in <a href="https://copticscriptorium.org" target="_blank" rel="noreferrer">Coptic Scriptorium</a> data. Correspondences between nodes in different phrases are computed using dependency parses based on <a href="https://copticscriptorium.org/treebank.html" target="_blank" rel="noreferrer">the Coptic Universal Dependency Treebank</a>.
              <br />
              <strong>Disclaimer:</strong> some errors due to automatic Natural Language Processing may be included in this graph, which is provided as an assistive tool only.
            </div>
          </div>
        </div>
      )}
    </>
  );
}