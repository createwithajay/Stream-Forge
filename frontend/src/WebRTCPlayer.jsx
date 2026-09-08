import {useEffect,useRef,useState}from "react";

function WebRTCPlayer() {
  const videoRef = useRef(null);
  const [status, setStatus] = useState("Connecting...");

  useEffect(() => {
    let peerConnection;

    async function startWebRTC() {
      try {
        peerConnection = new RTCPeerConnection();

        peerConnection.ontrack = (event) => {
          if (videoRef.current) {
            videoRef.current.srcObject = event.streams[0];
            setStatus("LIVE");
          }
        };

        // Ask the backend for a video stream.
        peerConnection.addTransceiver("video", {
          direction: "recvonly",
        });

        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);

        const response = await fetch(
          "http://127.0.0.1:8000/api/webrtc/offer",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              sdp: peerConnection.localDescription.sdp,
              type: peerConnection.localDescription.type,
            }),
          }
        );

        if (!response.ok) {
          throw new Error("WebRTC connection failed");
        }

        const answer = await response.json();

        await peerConnection.setRemoteDescription(
          new RTCSessionDescription(answer)
        );
      } catch (error) {
        console.error("WebRTC error:", error);
        setStatus("OFFLINE");
      }
    }

    startWebRTC();

    return () => {
      if (peerConnection) {
        peerConnection.close();
      }
    };
  }, []);

  return (
    <div className="webrtc-player">
      <div className="webrtc-header">
        <h3>WebRTC Test Stream</h3>
        <span>● {status}</span>
      </div>

      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        style={{
          width: "100%",
          borderRadius: "8px",
          background: "#000",
        }}
      />
    </div>
  );
}

export default WebRTCPlayer;