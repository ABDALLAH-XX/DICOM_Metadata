import { useState, useEffect } from 'react';

function App() {
  const [slices, setSlices] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [imageIndex, setImageIndex] = useState(0); // Specific index for debouncing images
  const [loading, setLoading] = useState(true);

  // 1. Fetch the complete list of slices on component mount
  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/slices')
      .then((res) => res.json())
      .then((data) => {
        setSlices(data);
        setLoading(false);
      })
      .catch((err) => console.error("API Error:", err));
  }, []);

  // 2. DEBOUNCING EFFECT: Delays image loading by 40ms 
  // to avoid slamming the Python backend while sliding quickly
  useEffect(() => {
    if (slices.length === 0) return;
    
    const timeoutId = setTimeout(() => {
      setImageIndex(currentIndex);
    }, 40); // 40 milliseconds (smooth to the eye, lightweight for the CPU)

    return () => clearTimeout(timeoutId);
  }, [currentIndex, slices]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', fontFamily: 'sans-serif' }}>
        <h3>Loading cranial database...</h3>
      </div>
    );
  }

  // Text metadata updates INSTANTLY for real-time responsiveness
  const activeSliceText = slices[currentIndex];
  
  // Image updates with the slight debounced delay
  const activeSliceImage = slices[imageIndex];
  const urlImage = activeSliceImage 
    ? `http://127.0.0.1:8000/api/slices/${activeSliceImage.instance_number}/image`
    : '';

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', padding: '20px', fontFamily: 'sans-serif', color: '#333' }}>
      <header style={{ borderBottom: '2px solid #eee', marginBottom: '20px' }}>
        <h2>Mini-PACS: 2D Cranial Visualizer</h2>
        <p style={{ color: '#666' }}>Total volume: <strong>{slices.length} slices</strong> spatially indexed</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px', alignItems: 'start' }}>
        
        {/* --- LEFT COLUMN: DICOM IMAGE DISPLAY --- */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', backgroundColor: '#111', padding: '15px', borderRadius: '8px' }}>
          <div style={{ width: '512px', height: '512px', display: 'flex', justifyContent: 'center', alignItems: 'center', overflow: 'hidden' }}>
            {urlImage ? (
              <img 
                src={urlImage} 
                alt="DICOM Slice" 
                style={{ width: '512px', height: '512px', objectFit: 'contain' }}
              />
            ) : (
              <div style={{ color: '#fff' }}>No Image Loaded</div>
            )}
          </div>
          
          {/* THE INTERACTIVE SLIDER */}
          <div style={{ width: '100%', marginTop: '20px', color: '#fff' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', textAlign: 'center' }}>
              Anatomical Navigation (Z-Axis)
            </label>
            <input 
              type="range" 
              min="0" 
              max={slices.length - 1} 
              value={currentIndex} 
              onChange={(e) => setCurrentIndex(parseInt(e.target.value))}
              style={{ width: '100%', cursor: 'pointer' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#aaa', marginTop: '5px' }}>
              <span>Base of Skull</span>
              <span>Slice {currentIndex + 1} / {slices.length}</span>
              <span>Top of Skull</span>
            </div>
          </div>
        </div>

        {/* --- RIGHT COLUMN: METADATA PANEL --- */}
        <div style={{ backgroundColor: '#fff', border: '1px solid #ddd', padding: '20px', borderRadius: '8px', width: '100%' }}>
          <h3 style={{ marginTop: 0, color: '#0056b3', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
            Slice Metadata
          </h3>
          {activeSliceText && (
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
              <tbody>
                <tr style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '10px 0', fontWeight: 'bold', color: '#555' }}>File Name:</td>
                  <td style={{ padding: '10px 0', fontFamily: 'monospace', fontSize: '13px' }}>{activeSliceText.file_name}</td>
                </tr>
                <tr style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '10px 0', fontWeight: 'bold', color: '#555' }}>Instance Number:</td>
                  <td style={{ padding: '10px 0' }}>{activeSliceText.instance_number}</td>
                </tr>
                <tr style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '10px 0', fontWeight: 'bold', color: '#555' }}>Spatial Position Z:</td>
                  <td style={{ padding: '10px 0', color: '#d9534f', fontWeight: 'bold' }}>{activeSliceText.slice_location_z} mm</td>
                </tr>
                <tr style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '10px 0', fontWeight: 'bold', color: '#555' }}>Slice Thickness:</td>
                  <td style={{ padding: '10px 0' }}>{activeSliceText.slice_thickness} mm</td>
                </tr>
              </tbody>
            </table>
          )}
        </div>

      </div>
    </div>
  );
}

export default App;