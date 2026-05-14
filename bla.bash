#!/bin/bash     
# Find the entire second body section to replace
start_tag = '                      <a:r>\n                        <a:rPr b="1" lang="tr-TR" sz="3600" spc="-1" strike="noStrike">\n                          <a:solidFill>\n                            <a:srgbClr val="ff0000"/>\n                          </a:solidFill>\n                          <a:latin typeface="Calibri"/>\n                        </a:rPr>\n                        <a:t>Proje sergisinde yer alacak posterin özellikleri aşağıda verilmiştir.</a:t>\n                      </a:r>\n                      <a:endParaRPr b="0" lang="en-US" sz="3600" spc="-1" strike="noStrike">\n                        <a:solidFill>\n                          <a:srgbClr val="000000"/>\n                        </a:solidFill>\n                        <a:latin typeface="Calibri"/>\n                      </a:endParaRPr>\n                    </a:p>'

end_tag = '                        <a:t>Poster, açık ve net olarak okunacak şekilde hazırlanmalıdır.</a:t>\n                      </a:r>\n                      <a:endParaRPr b="0" lang="en-US" sz="3600" spc="-1" strike="noStrike">\n                        <a:solidFill>\n                          <a:srgbClr val="000000"/>\n                        </a:solidFill>\n                        <a:latin typeface="Calibri"/>\n                      </a:endParaRPr>\n                    </a:p>'

si = content.find(start_tag)
ei = content.find(end_tag) + len(end_tag)

print(f"start: {si}, end: {ei}, length: {ei-si}")
print("unique start:", content.count(start_tag))

new_content = """                    <a:p>
                      <a:pPr algn="just"><a:tabLst><a:tab algn="l" pos="0"/></a:tabLst></a:pPr>
                      <a:r><a:rPr b="1" lang="en-US" sz="3300" spc="-1" strike="noStrike"><a:solidFill><a:srgbClr val="1f497d"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>Core Components</a:t></a:r>
                    </a:p>
                    <a:p>
                      <a:pPr algn="just"><a:tabLst><a:tab algn="l" pos="0"/></a:tabLst></a:pPr>
                      <a:r><a:rPr b="1" lang="en-US" sz="3000" spc="-1" strike="noStrike"><a:solidFill><a:srgbClr val="000000"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>Orchestrator (main.py): </a:t></a:r>
                      <a:r><a:rPr b="0" lang="en-US" sz="3000" spc="-1" strike="noStrike"><a:solidFill><a:srgbClr val="000000"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>Manages the full pipeline from user speech to audio response.</a:t></a:r>
                    </a:p>
                    <a:p>
                      <a:pPr algn="just"><a:tabLst><a:tab algn="l" pos="0"/></a:tabLst></a:pPr>
                      <a:r><a:rPr b="1" lang="en-US" sz="3000" spc="-1" strike="noStrike"><a:solidFill><a:srgbClr val="000000"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>AI Logic (Google Gemini): </a:t></a:r>
                      <a:r><a:rPr b="0" lang="en-US" sz="3000" spc="-1" strike="noStrike"><a:solidFill><a:srgbClr val="000000"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>Conversational AI with context memory and multi-key rate limiting.</a:t></a:r>
                    </a:p>
                    <a:p>
                      <a:pPr algn="just"><a:tabLst><a:tab algn="l" pos="0"/></a:tabLst></a:pPr>
                      <a:r><a:rPr b="1" lang="en-US" sz="3000" spc="-1" strike="noStrike"><a:solidFill><a:srgbClr val="000000"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>Vector Database (SQLite + sqlite-vec): </a:t></a:r>
                      <a:r><a:rPr b="0" lang="en-US" sz="3000" spc="-1" strike="noStrike"><a:solidFill><a:srgbClr val="000000"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>768-dim semantic embeddings for recipe search across 25+ attributes.</a:t></a:r>
                    </a:p>
                    <a:p>
                      <a:pPr algn="just"><a:tabLst><a:tab algn="l" pos="0"/></a:tabLst></a:pPr>
                      <a:r><a:rPr b="1" lang="en-US" sz="3000" spc="-1" strike="noStrike"><a:solidFill><a:srgbClr val="000000"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>Speech (Piper TTS / Kaldi STT): </a:t></a:r>
                      <a:r><a:rPr b="0" lang="en-US" sz="3000" spc="-1" strike="noStrike"><a:solidFill><a:srgbClr val="000000"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>Full offline-capable voice I/O via browser and desktop.</a:t></a:r>
                    </a:p>
                    <a:p>
                      <a:pPr algn="just"><a:tabLst><a:tab algn="l" pos="0"/></a:tabLst></a:pPr>
                      <a:r><a:rPr b="1" lang="en-US" sz="3000" spc="-1" strike="noStrike"><a:solidFill><a:srgbClr val="000000"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>Web API (Flask + SocketIO): </a:t></a:r>
                      <a:r><a:rPr b="0" lang="en-US" sz="3000" spc="-1" strike="noStrike"><a:solidFill><a:srgbClr val="000000"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>Real-time bidirectional browser-desktop communication.</a:t></a:r>
                    </a:p>
                    <a:p>
                      <a:pPr algn="just"><a:tabLst><a:tab algn="l" pos="0"/></a:tabLst></a:pPr>
                      <a:endParaRPr b="0" lang="en-US" sz="3000" spc="-1" strike="noStrike"><a:solidFill><a:srgbClr val="000000"/></a:solidFill><a:latin typeface="Calibri"/></a:endParaRPr>
                    </a:p>
                    <a:p>
                      <a:pPr algn="just"><a:tabLst><a:tab algn="l" pos="0"/></a:tabLst></a:pPr>
                      <a:r><a:rPr b="1" lang="en-US" sz="3300" spc="-1" strike="noStrike"><a:solidFill><a:srgbClr val="1f497d"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>Tech Stack</a:t></a:r>
                    </a:p>
                    <a:p>
                      <a:pPr algn="just"><a:tabLst><a:tab algn="l" pos="0"/></a:tabLst></a:pPr>
                      <a:r><a:rPr b="0" lang="en-US" sz="3000" spc="-1" strike="noStrike"><a:solidFill><a:srgbClr val="000000"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>Python 3 &#x2022; Google Gemini API &#x2022; SQLite + sqlite-vec &#x2022; Flask &#x2022; SocketIO &#x2022; Piper TTS &#x2022; Kaldi STT &#x2022; OpenCV &#x2022; scikit-learn &#x2022; NumPy &#x2022; Tkinter</a:t></a:r>
                    </a:p>"""

EOF