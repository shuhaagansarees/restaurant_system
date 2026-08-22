function toggleDropdown(id) {
            document.getElementById(id).classList.toggle('active');
        }
        window.onclick = function(event) {
            if (!event.target.matches('.profile-circle')) {
                var dropdowns = document.getElementsByClassName("dropdown");
                for (var i = 0; i < dropdowns.length; i++) {
                    var openDropdown = dropdowns[i];
                    if (openDropdown.classList.contains('active')) {
                        openDropdown.classList.remove('active');
                    }
                }
            }
        }
        
        function toggleSidebar(forceState) {
            const sidebar = document.querySelector('.sidebar');
            const overlay = document.getElementById('sidebarOverlay');
            if (!sidebar) return;
            
            if (typeof forceState === 'boolean') {
                if (forceState) {
                    sidebar.classList.add('active');
                    if (overlay) overlay.classList.add('active');
                    document.body.classList.add('drawer-open');
                } else {
                    sidebar.classList.remove('active');
                    if (overlay) overlay.classList.remove('active');
                    document.body.classList.remove('drawer-open');
                }
            } else {
                const isActive = sidebar.classList.toggle('active');
                if (overlay) overlay.classList.toggle('active', isActive);
                document.body.classList.toggle('drawer-open', isActive);
            }
        }

        // Anti-DevTools Deterrent
        document.addEventListener('keydown', event => {
            if (event.keyCode === 123 || (event.ctrlKey && event.shiftKey && (event.keyCode === 73 || event.keyCode === 74 || event.keyCode === 67)) || (event.ctrlKey && event.keyCode === 85)) {
                try{event.preventDefault();}catch(e){}
                console.warn("Unauthorized access prohibited.");
            }
        });
function openModal(id) {
            document.getElementById(id).classList.add('active');
        }
        function closeModal(id) {
            document.getElementById(id).classList.remove('active');
        }

        function openNewOrderModal() {
            openModal('newOrderModal');
        }

        function handleTopBillSearch(e) {
            if (e.key === 'Enter') {
                const val = document.getElementById('topBillSearchInput').value.trim();
                if (val) {
                    document.getElementById('modalBillQueryInput').value = val;
                    openModal('billSearchModal');
                    performBillSearch();
                }
            }
        }

        function handleTopKotSearch(e) {
            if (e.key === 'Enter') {
                const val = document.getElementById('topKotSearchInput').value.trim();
                if (val) {
                    document.getElementById('modalKotQueryInput').value = val;
                    openModal('kotSearchModal');
                    performKotSearch();
                }
            }
        }

        async function performBillSearch() {
            const query = document.getElementById('modalBillQueryInput').value.trim();
            const container = document.getElementById('billSearchResults');
            if (!query) return;
            container.innerHTML = '<p style="text-align:center; color:#94a3b8; padding:20px;">Searching...</p>';
            try {
                const res = await fetch(`/api/search_bill?q=${encodeURIComponent(query)}`);
                const data = await res.json();
                if (!data.invoices || data.invoices.length === 0) {
                    container.innerHTML = '<p style="text-align:center; color:#ef4444; padding:20px;">No invoices found matching query.</p>';
                    return;
                }
                let html = '<div style="display:flex; flex-direction:column; gap:10px;">';
                data.invoices.forEach(inv => {
                    html += `
                    <div style="background:#f8fafc; border:1px solid #e2e8f0; padding:12px 16px; border-radius:8px; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-weight:700; color:#1e293b;">#${inv.invoice_number} <span style="font-weight:400; color:#64748b; font-size:0.8rem;">(${inv.date})</span></div>
                            <div style="font-size:0.8rem; color:#475569; margin-top:2px;">Customer: ${inv.customer || 'Walk-in'} &bull; Payment: <span style="text-transform:uppercase; font-weight:600;">${inv.payment_method}</span></div>
                            <div style="font-size:0.95rem; font-weight:700; color:#dc2626; margin-top:4px;">₹${inv.total}</div>
                        </div>
                        <div style="display:flex; gap:8px;">
                            <a href="/admin/invoice/print/${inv.id}" target="_blank" class="btn-primary" style="padding:6px 12px; font-size:0.8rem; text-decoration:none; display:flex; align-items:center; gap:5px;"><i class="fa-solid fa-print"></i> Print</a>
                        </div>
                    </div>`;
                });
                html += '</div>';
                container.innerHTML = html;
            } catch (err) {
                container.innerHTML = '<p style="text-align:center; color:#ef4444; padding:20px;">Error searching bills.</p>';
            }
        }

        async function performKotSearch() {
            const query = document.getElementById('modalKotQueryInput').value.trim();
            const container = document.getElementById('kotSearchResults');
            if (!query) return;
            container.innerHTML = '<p style="text-align:center; color:#94a3b8; padding:20px;">Searching KOTs...</p>';
            try {
                const res = await fetch(`/api/search_kot?q=${encodeURIComponent(query)}`);
                const data = await res.json();
                if (!data.kots || data.kots.length === 0) {
                    container.innerHTML = '<p style="text-align:center; color:#ef4444; padding:20px;">No KOT tickets found.</p>';
                    return;
                }
                let html = '<div style="display:flex; flex-direction:column; gap:10px;">';
                data.kots.forEach(k => {
                    html += `
                    <div style="background:#f8fafc; border:1px solid #e2e8f0; padding:12px 16px; border-radius:8px; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-weight:700; color:#1e293b;">KOT #${k.kot_number} &bull; Table: ${k.table_name || 'Parcel'}</div>
                            <div style="font-size:0.8rem; color:#64748b; margin-top:2px;">Order ID: #${k.order_id} &bull; Items: ${k.items_summary}</div>
                            <div style="font-size:0.8rem; font-weight:600; color:#16a34a; margin-top:4px;">Status: ${k.status}</div>
                        </div>
                        <div>
                            <a href="/admin/kot/print/${k.order_id}?kot=${k.kot_number}" target="_blank" class="btn-primary" style="padding:6px 12px; font-size:0.8rem; text-decoration:none; background:#ea580c; border-color:#ea580c; display:flex; align-items:center; gap:5px;"><i class="fa-solid fa-print"></i> Print KOT</a>
                        </div>
                    </div>`;
                });
                html += '</div>';
                container.innerHTML = html;
            } catch (err) {
                container.innerHTML = '<p style="text-align:center; color:#ef4444; padding:20px;">Error searching KOTs.</p>';
            }
        }

        async function openItemOnOffModal() {
            openModal('itemOnOffModal');
            const tbody = document.getElementById('itemOnOffTableBody');
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:30px; color:#94a3b8;">Loading items...</td></tr>';
            try {
                const res = await fetch('/api/all_items_status');
                const data = await res.json();
                let html = '';
                data.items.forEach(itm => {
                    html += `
                    <tr class="item-row" data-name="${itm.name.toLowerCase()}" data-cat="${itm.category.toLowerCase()}" style="border-bottom:1px solid #e2e8f0;">
                        <td style="padding:10px 14px; font-weight:600; color:#1e293b;">${itm.name}</td>
                        <td style="padding:10px 14px; color:#64748b;">${itm.category}</td>
                        <td style="padding:10px 14px; font-weight:600;">₹${itm.price}</td>
                        <td style="padding:10px 14px; text-align:center;">
                            <span id="badge-${itm.id}" style="padding:3px 8px; border-radius:12px; font-size:0.72rem; font-weight:700; background:${itm.is_available ? '#dcfce7' : '#fee2e2'}; color:${itm.is_available ? '#166534' : '#991b1b'};">
                                ${itm.is_available ? 'Available' : 'Unavailable'}
                            </span>
                        </td>
                        <td style="padding:10px 14px; text-align:center;">
                            <input type="checkbox" ${itm.is_available ? 'checked' : ''} onchange="toggleItemAvailability(${itm.id}, this.checked)" style="transform:scale(1.3); cursor:pointer; accent-color:#16a34a;">
                        </td>
                    </tr>`;
                });
                tbody.innerHTML = html;
            } catch (err) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#ef4444; padding:20px;">Failed to load items.</td></tr>';
            }
        }

        function filterModalItems() {
            const q = document.getElementById('itemFilterInput').value.toLowerCase();
            document.querySelectorAll('#itemOnOffTableBody .item-row').forEach(row => {
                const name = row.getAttribute('data-name');
                const cat = row.getAttribute('data-cat');
                if (name.includes(q) || cat.includes(q)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }

        async function toggleItemAvailability(itemId, isAvailable) {
            const badge = document.getElementById(`badge-${itemId}`);
            if (badge) {
                badge.style.background = isAvailable ? '#dcfce7' : '#fee2e2';
                badge.style.color = isAvailable ? '#166534' : '#991b1b';
                badge.innerText = isAvailable ? 'Available' : 'Unavailable';
            }
            const token = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            await fetch('/api/toggle_item', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': token },
                body: JSON.stringify({ item_id: itemId, is_available: isAvailable })
            });
        }

        async function openRecentInvoicesModal() {
            openModal('recentInvoicesModal');
            const body = document.getElementById('recentInvoicesBody');
            body.innerHTML = '<p style="text-align:center; color:#94a3b8; padding:30px;">Loading recent invoices...</p>';
            try {
                const res = await fetch('/api/recent_invoices');
                const data = await res.json();
                if (!data.invoices || data.invoices.length === 0) {
                    body.innerHTML = '<p style="text-align:center; color:#64748b; padding:30px;">No recent invoices today.</p>';
                    return;
                }
                let html = '<div style="display:flex; flex-direction:column; gap:10px;">';
                data.invoices.forEach(inv => {
                    html += `
                    <div style="background:#f8fafc; border:1px solid #e2e8f0; padding:12px 16px; border-radius:8px; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-weight:700; color:#1e293b;">#${inv.invoice_number} &bull; ₹${inv.total}</div>
                            <div style="font-size:0.8rem; color:#64748b; margin-top:2px;">Paid via <strong style="text-transform:uppercase;">${inv.payment_method}</strong> &bull; ${inv.time_ago}</div>
                        </div>
                        <a href="/admin/invoice/print/${inv.id}" target="_blank" class="btn-primary" style="padding:6px 12px; font-size:0.8rem; text-decoration:none;"><i class="fa-solid fa-print"></i> Print</a>
                    </div>`;
                });
                html += '</div>';
                body.innerHTML = html;
            } catch (err) {
                body.innerHTML = '<p style="text-align:center; color:#ef4444; padding:30px;">Error loading recent invoices.</p>';
            }
        }

        async function openHoldOrdersModal() {
            openModal('holdOrdersModal');
            const body = document.getElementById('holdOrdersBody');
            body.innerHTML = '<p style="text-align:center; color:#94a3b8; padding:30px;">Loading active orders...</p>';
            try {
                const res = await fetch('/api/hold_orders');
                const data = await res.json();
                if (!data.orders || data.orders.length === 0) {
                    body.innerHTML = '<p style="text-align:center; color:#64748b; padding:30px;">No active held table orders.</p>';
                    return;
                }
                let html = '<div style="display:flex; flex-direction:column; gap:10px;">';
                data.orders.forEach(o => {
                    html += `
                    <div style="background:#f8fafc; border:1px solid #e2e8f0; padding:12px 16px; border-radius:8px; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-weight:700; color:#1e293b;">Table ${o.table_name} &bull; Order #${o.id}</div>
                            <div style="font-size:0.8rem; color:#64748b; margin-top:2px;">Status: <span style="font-weight:600; color:#ea580c; text-transform:uppercase;">${o.status}</span> &bull; Items: ${o.items_count}</div>
                            <div style="font-size:0.9rem; font-weight:700; color:#1e293b; margin-top:2px;">Amount: ₹${o.total_amount}</div>
                        </div>
                        <div style="display:flex; gap:8px;">
                            <a href="/admin/edit_order/${o.id}" class="btn-primary" style="padding:6px 12px; font-size:0.8rem; text-decoration:none;"><i class="fa-solid fa-pen"></i> Edit</a>
                        </div>
                    </div>`;
                });
                html += '</div>';
                body.innerHTML = html;
            } catch (err) {
                body.innerHTML = '<p style="text-align:center; color:#ef4444; padding:30px;">Error loading hold orders.</p>';
            }
        }

        function openAlertsModal() {
            openModal('alertsModal');
        }

        // ==========================================
        // GLOBAL REAL-TIME WAITER CALL & AUDIO CHIME
        // ==========================================
        let activeWaiterCalls = [];

        function playWaiterChimeSound() {
            try {
                const AudioCtx = window.AudioContext || window.webkitAudioContext;
                if (AudioCtx) {
                    const ctx = new AudioCtx();
                    if (ctx.state === 'suspended') {
                        ctx.resume();
                    }
                    const now = ctx.currentTime;
                    
                    // Dual Tone Crystal Bell Chime
                    // Tone 1: 880 Hz (A5)
                    const osc1 = ctx.createOscillator();
                    const gain1 = ctx.createGain();
                    osc1.type = 'sine';
                    osc1.frequency.setValueAtTime(880, now);
                    gain1.gain.setValueAtTime(0.45, now);
                    gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
                    osc1.connect(gain1);
                    gain1.connect(ctx.destination);
                    osc1.start(now);
                    osc1.stop(now + 0.6);

                    // Tone 2: 1318.51 Hz (E6) high harmonic crystal ping
                    const osc2 = ctx.createOscillator();
                    const gain2 = ctx.createGain();
                    osc2.type = 'triangle';
                    osc2.frequency.setValueAtTime(1318.51, now + 0.12);
                    gain2.gain.setValueAtTime(0.4, now + 0.12);
                    gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.8);
                    osc2.connect(gain2);
                    gain2.connect(ctx.destination);
                    osc2.start(now + 0.12);
                    osc2.stop(now + 0.8);
                }
            } catch(e) {
                console.log("WebAudio notice:", e);
            }
        }

        async function loadPendingWaiterCalls() {
            try {
                const res = await fetch('/api/pending_waiter_calls');
                const data = await res.json();
                if (data.success) {
                    activeWaiterCalls = data.calls || [];
                    updateWaiterCallsUI();
                }
            } catch (e) {
                console.log("Error loading pending calls:", e);
            }
        }

        function updateWaiterCallsUI() {
            const badge = document.getElementById('waiterCallsToolBadge');
            const icon = document.getElementById('waiterCallsIcon');
            if (badge) {
                if (activeWaiterCalls.length > 0) {
                    badge.innerText = activeWaiterCalls.length;
                    badge.style.display = 'inline-block';
                    if (icon) icon.classList.add('fa-bounce');
                } else {
                    badge.style.display = 'none';
                    if (icon) icon.classList.remove('fa-bounce');
                }
            }
            
            const modalBody = document.getElementById('waiterCallsModalBody');
            if (modalBody) {
                if (activeWaiterCalls.length === 0) {
                    modalBody.innerHTML = `
                        <div style="text-align:center; padding:30px; color:#64748b;">
                            <i class="fa-solid fa-circle-check" style="font-size:2.5rem; color:#10b981; margin-bottom:10px;"></i>
                            <p style="font-weight:600; margin:0; font-size:1rem; color:#1e293b;">All tables attended!</p>
                            <small>No pending customer calls.</small>
                        </div>
                    `;
                } else {
                    let html = '<div style="display:flex; flex-direction:column; gap:10px;">';
                    activeWaiterCalls.forEach(c => {
                        html += `
                            <div id="modal-call-${c.id}" style="background:#fff; border:2px solid #fecaca; border-radius:10px; padding:12px 16px; display:flex; justify-content:space-between; align-items:center; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                                <div style="display:flex; align-items:center; gap:12px;">
                                    <div style="background:#fee2e2; color:#ef4444; width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.2rem;">
                                        <i class="fa-solid fa-bell"></i>
                                    </div>
                                    <div>
                                        <strong style="font-size:1.05rem; color:#1e293b;">Table ${c.table_name}</strong>
                                        <div style="font-size:0.8rem; color:#64748b;">Called at ${c.time}</div>
                                    </div>
                                </div>
                                <button onclick="globalResolveWaiterCall(${c.id}, '${c.table_name}')" style="background:#10b981; color:#fff; border:none; padding:7px 14px; border-radius:6px; font-weight:700; cursor:pointer; font-size:0.85rem; display:flex; align-items:center; gap:5px;">
                                    <i class="fa-solid fa-check"></i> Attended
                                </button>
                            </div>
                        `;
                    });
                    html += '</div>';
                    modalBody.innerHTML = html;
                }
            }

            if (typeof highlightLiveTablesCalls === 'function') {
                highlightLiveTablesCalls(activeWaiterCalls);
            }
        }

        function showWaiterCallFloatingToast(call) {
            const container = document.getElementById('globalWaiterCallContainer');
            if (!container) return;
            if (document.getElementById(`floating-call-${call.id}`)) return;

            const toast = document.createElement('div');
            toast.id = `floating-call-${call.id}`;
            toast.style.cssText = `
                pointer-events: auto;
                background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);
                color: #ffffff;
                padding: 16px 18px;
                border-radius: 12px;
                box-shadow: 0 12px 30px -5px rgba(220, 38, 38, 0.55);
                font-family: 'Inter', sans-serif;
                animation: slideInUp 0.35s cubic-bezier(0.16, 1, 0.3, 1);
                border: 2px solid #fecaca;
            `;
            toast.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px;">
                    <div style="display:flex; align-items:center; gap:12px;">
                        <span style="font-size:1.8rem; line-height:1;">[Bell]</span>
                        <div>
                            <div style="font-size:1.15rem; font-weight:800; letter-spacing:-0.3px;">Table ${call.table_name}</div>
                            <div style="font-size:0.82rem; opacity:0.95; font-weight:500;">Calling for Assistance &bull; ${call.time}</div>
                        </div>
                    </div>
                </div>
                <div style="margin-top:12px; display:flex; justify-content:flex-end; gap:8px;">
                    <button onclick="globalResolveWaiterCall(${call.id}, '${call.table_name}')" style="background:#ffffff; color:#b91c1c; border:none; padding:7px 16px; border-radius:8px; font-size:0.85rem; font-weight:800; cursor:pointer; display:flex; align-items:center; gap:5px; box-shadow:0 2px 5px rgba(0,0,0,0.15);">
                        <i class="fa-solid fa-check"></i> Mark Attended
                    </button>
                </div>
            `;
            container.appendChild(toast);
        }

        async function globalResolveWaiterCall(callId, tableName) {
            try {
                const res = await fetch(`/api/resolve_call/${callId}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                const data = await res.json();
                if (data.success) {
                    activeWaiterCalls = activeWaiterCalls.filter(c => c.id !== callId);
                    const toast = document.getElementById(`floating-call-${callId}`);
                    if (toast) toast.remove();
                    updateWaiterCallsUI();
                }
            } catch(e) {
                console.log("Error resolving waiter call:", e);
            }
        }

        function openWaiterCallsModal() {
            openModal('waiterCallsModal');
            loadPendingWaiterCalls();
        }

        // Global Real-time Sockets
        window.socket = window.socket || (typeof io !== 'undefined' ? io() : null);
        if (window.socket) {
            window.socket.on('new_waiter_call', function(data) {
                console.log("[Bell] Global Waiter Call Received:", data);
                playWaiterChimeSound();
                if (!activeWaiterCalls.some(c => c.id === data.id)) {
                    activeWaiterCalls.unshift(data);
                }
                showWaiterCallFloatingToast(data);
                updateWaiterCallsUI();
            });

            window.socket.on('waiter_call_resolved', function(data) {
                console.log("✅ Global Waiter Call Resolved:", data);
                activeWaiterCalls = activeWaiterCalls.filter(c => c.id !== data.id);
                const toast = document.getElementById(`floating-call-${data.id}`);
                if (toast) toast.remove();
                updateWaiterCallsUI();
            });

            window.socket.on('inventory_alert', function(data) {
                console.warn('[INVENTORY ALERT]', data);
                try {
                    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                    const osc = audioCtx.createOscillator();
                    const gain = audioCtx.createGain();
                    osc.type = 'triangle';
                    osc.frequency.setValueAtTime(587.33, audioCtx.currentTime);
                    osc.frequency.setValueAtTime(880.00, audioCtx.currentTime + 0.15);
                    gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
                    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);
                    osc.connect(gain);
                    gain.connect(audioCtx.destination);
                    osc.start();
                    osc.stop(audioCtx.currentTime + 0.5);
                } catch (e) {}

                const badge = document.getElementById('alertsToolBadge');
                if (badge) {
                    let currentCount = parseInt(badge.innerText) || 0;
                    badge.innerText = currentCount + 1;
                    badge.style.display = 'inline-block';
                }

                let toastBox = document.getElementById('inventoryAlertToastContainer');
                if (!toastBox) {
                    toastBox = document.createElement('div');
                    toastBox.id = 'inventoryAlertToastContainer';
                    toastBox.style.cssText = 'position:fixed; top:75px; right:20px; z-index:999999; display:flex; flex-direction:column; gap:12px; max-width:380px; pointer-events:none;';
                    document.body.appendChild(toastBox);
                }

                const toast = document.createElement('div');
                toast.style.cssText = 'pointer-events:auto; background:#fff1f2; border:2px solid #f43f5e; color:#9f1239; padding:14px 18px; border-radius:10px; box-shadow:0 10px 25px -5px rgba(225,29,72,0.3); font-family:Inter,sans-serif; animation:slideInRight 0.3s cubic-bezier(0.16, 1, 0.3, 1);';
                toast.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <i class="fa-solid fa-triangle-exclamation" style="font-size:1.2rem; color:#e11d48;"></i>
                            <strong style="font-size:0.95rem; color:#9f1239;">Low Stock Warning!</strong>
                        </div>
                        <button onclick="this.parentElement.parentElement.remove()" style="background:none; border:none; color:#9f1239; cursor:pointer; font-size:1rem;">&times;</button>
                    </div>
                    <div style="margin-top:6px; font-size:0.85rem; font-weight:600; color:#881337;">
                        ${data.name} has only <span style="background:#ffe4e6; color:#e11d48; padding:2px 6px; border-radius:4px; font-weight:800;">${data.current_stock} ${data.unit || 'pcs'}</span> left!
                    </div>
                    <div style="margin-top:10px; display:flex; justify-content:flex-end; gap:8px;">
                        <a href="/admin/inventory" style="background:#e11d48; color:#ffffff; padding:5px 12px; border-radius:6px; font-size:0.78rem; text-decoration:none; font-weight:700; display:inline-flex; align-items:center; gap:4px;">
                            <i class="fa-solid fa-boxes-stacked"></i> Restock Now
                        </a>
                    </div>
                `;
                toastBox.appendChild(toast);

                setTimeout(() => {
                    if (toast && toast.parentElement) {
                        toast.style.opacity = '0';
                        toast.style.transform = 'translateX(50px)';
                        toast.style.transition = 'all 0.4s ease';
                        setTimeout(() => toast.remove(), 400);
                    }
                }, 10000);
            });
        }

        // Auto-load pending waiter calls on every admin page load
        document.addEventListener('DOMContentLoaded', function() {
            loadPendingWaiterCalls();
        });
// Make all tables responsive on mobile by wrapping them in a scrollable div
        document.addEventListener('DOMContentLoaded', function() {
            const tables = document.querySelectorAll('table:not(.no-responsive)');
            tables.forEach(table => {
                if (!table.parentElement.classList.contains('table-responsive')) {
                    const wrapper = document.createElement('div');
                    wrapper.className = 'table-responsive';
                    wrapper.style.cssText = 'overflow-x: auto; -webkit-overflow-scrolling: touch; width: 100%; border-radius: 8px; margin-bottom: 15px;';
                    table.parentNode.insertBefore(wrapper, table);
                    wrapper.appendChild(table);
                }
            });
        });
var socket = window.socket || (typeof io !== 'undefined' ? io() : null);
    
    let currentSettleOrder = null;
    let currentSettleOrderId = null;
    let currentSettleOrderTotal = 0;
    let currentSettleCoupon = '';
    let currentSettleMobile = '';
    let currentAvailablePoints = 0;
    
    // Discount variables
    let appliedDiscountType = null;
    let appliedDiscountValue = 0;
    let appliedDiscountReason = '';
    let orderItemsMap = {}; // orderId -> items

    // Fix for mobile devices: when screen wakes up or tab becomes visible, reload to fetch missed real-time events
    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") {
            window.location.reload();
        }
    });

    function closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
        }
    }

    async function openSettleModal(orderId, type, customerName, customerMobile, totalStr, coupon) {
        currentSettleOrderId = orderId;
        currentSettleOrderTotal = parseFloat(totalStr);
        currentSettleCoupon = coupon || '';
        currentSettleMobile = customerMobile || '';
        
        appliedDiscountType = null;
        appliedDiscountValue = 0;
        appliedDiscountReason = '';
        
        document.getElementById('settle-order-title').innerText = `Order #${orderId}`;
        document.getElementById('settle-total-display').innerText = currentSettleOrderTotal.toFixed(2);
        
        document.getElementById('settle-amount').value = currentSettleOrderTotal.toFixed(2);
        document.getElementById('settle-customer-paid').value = '';
        document.getElementById('settle-return-display').innerText = '₹0';
        document.getElementById('settle-return-display').style.color = 'var(--text-color)';
        document.getElementById('settle-coupon').value = '';
        document.getElementById('settle-redeem-points').value = '';
        document.getElementById('settle-loyalty-section').style.display = 'none';

        if (currentSettleMobile) {
            try {
                const resp = await fetch('/api/customer/history?mobile=' + encodeURIComponent(currentSettleMobile));
                const data = await resp.json();
                if (data.success && data.loyalty_points > 0) {
                    currentAvailablePoints = data.loyalty_points;
                    document.getElementById('settle-available-points').innerText = data.loyalty_points;
                    document.getElementById('settle-redeem-points').max = data.loyalty_points;
                    document.getElementById('settle-loyalty-section').style.display = 'block';
                }
            } catch(e) { console.error('Error fetching loyalty points:', e); }
        }
        
        document.getElementById('settle-modal').classList.add('active');
    }
    
    function togglePaymentMethod() {
        const method = document.querySelector('input[name="payment-method"]:checked').value;
        const wrapper = document.getElementById('other-payment-wrapper');
        if (method === 'other') {
            wrapper.style.display = 'block';
        } else {
            wrapper.style.display = 'none';
        }
    }
    
    function calculateSettleChange() {
        const paidStr = document.getElementById('settle-customer-paid').value;
        const total = parseFloat(document.getElementById('settle-amount').value) || 0;
        const display = document.getElementById('settle-return-display');
        
        if (!paidStr) {
            display.innerText = '₹0';
            display.style.color = 'var(--text-color)';
            return;
        }
        
        const paid = parseFloat(paidStr);
        const diff = paid - total;
        
        if (diff < 0) {
            display.innerText = 'Less Amt.';
            display.style.color = '#dc2626'; // red
        } else {
            display.innerText = 'Return: ₹' + diff.toFixed(2);
            display.style.color = '#10b981'; // green
        }
    }

    function openDiscountModal() {
        document.getElementById('discount-modal').classList.add('active');
    }
    
    function saveDiscount() {
        const dReason = document.getElementById('discount-reason').value;
        const dType = document.querySelector('input[name="discount-type"]:checked').value;
        const dValue = parseFloat(document.getElementById('discount-value').value) || 0;
        
        if (dValue > 0) {
            appliedDiscountType = dType;
            appliedDiscountValue = dValue;
            appliedDiscountReason = dReason;
            
            let discountAmount = 0;
            // Reverse engineering subtotal from total: (total / 1.05)
            const subtotal = currentSettleOrderTotal / 1.05;
            if (dType === 'percent') {
                discountAmount = subtotal * (dValue / 100);
            } else {
                discountAmount = dValue;
            }
            
            const newSubtotal = subtotal - discountAmount;
            const newTotal = (newSubtotal * 1.05).toFixed(2);
            
            document.getElementById('settle-amount').value = newTotal;
            document.getElementById('settle-total-display').innerText = newTotal + " (Discounted)";
        }
        
        closeModal('discount-modal');
    }

    function applyPointsDiscount() {
        const redeemInput = document.getElementById('settle-redeem-points').value;
        const pts = parseInt(redeemInput);
        if (!pts || pts <= 0) return;
        
        if (pts > currentAvailablePoints) {
            alert('Cannot redeem more points than available!');
            document.getElementById('settle-redeem-points').value = currentAvailablePoints;
            return;
        }

        // Each point is Rs. 1 off (GST applies after discount)
        const subtotal = currentSettleOrderTotal / 1.05; 
        if (pts > subtotal) {
            alert('Discount cannot exceed the order subtotal!');
            return;
        }

        // Apply discount logic
        const discountAmt = pts;
        const newTotal = ((subtotal - discountAmt) * 1.05).toFixed(2);
        
        appliedDiscountType = 'loyalty';
        appliedDiscountValue = pts;
        appliedDiscountReason = `Redeemed ${pts} points`;

        document.getElementById('settle-amount').value = newTotal;
        document.getElementById('settle-total-display').innerText = newTotal + " (Points Redeemed)";
        calculateSettleChange();
        closeModal('discount-modal');
    }

    let currentSplitType = 'portion';
    let splitItemCounter = 0;
    
    function switchSplitTab(tab) {
        document.querySelectorAll('.split-tab').forEach(t => {
            t.classList.remove('active');
            t.style.color = 'var(--text-secondary)';
            t.style.borderBottom = 'none';
        });
        document.querySelectorAll('.split-content-pane').forEach(p => p.style.display = 'none');
        
        const selected = document.getElementById(`tab-${tab}`);
        selected.classList.add('active');
        selected.style.color = 'var(--brand-orange)';
        selected.style.borderBottom = '3px solid var(--brand-orange)';
        
        document.getElementById(`split-content-${tab}`).style.display = 'block';
        currentSplitType = tab;
    }
    
    async function openSplitModal() {
        document.getElementById('split-modal').classList.add('active');
        try {
            const resp = await fetch(`/api/order_details/${currentSettleOrderId}`);
            const data = await resp.json();
            if (data.success) {
                renderSplitItems(data.items);
            }
        } catch (e) {
            console.error(e);
        }
    }
    
    function renderSplitItems(items) {
        const list = document.getElementById('split-item-list');
        list.innerHTML = '';
        items.forEach((item, idx) => {
            for(let i=0; i<item.quantity; i++) {
                splitItemCounter++;
                list.innerHTML += `
                    <div class="split-item-row" data-id="${splitItemCounter}" data-menuid="${item.menu_item_id}" data-price="${item.price}" style="display:flex; gap:10px; padding:8px 0; border-bottom:1px solid var(--border-color);">
                        <input type="checkbox" class="split-item-chk" value="${splitItemCounter}">
                        <span>${item.name}</span>
                        <span style="margin-left:auto;">₹${item.price}</span>
                    </div>
                `;
            }
        });
    }
    
    function toggleAllSplitItems() {
        const checked = document.getElementById('split-all-items').checked;
        document.querySelectorAll('.split-item-chk').forEach(c => c.checked = checked);
    }
    
    function assignItemsToPart(partNumber) {
        const checked = document.querySelectorAll('#split-item-list .split-item-chk:checked');
        const partBox = document.getElementById(`part-items-${partNumber}`);
        
        checked.forEach(chk => {
            const row = chk.closest('.split-item-row');
            chk.checked = false;
            chk.style.display = 'none';
            partBox.appendChild(row);
        });
    }
    
    function addSplitPart() {
        const container = document.getElementById('split-parts-container');
        const currentParts = container.querySelectorAll('.split-part-box').length;
        const newPart = currentParts + 1;
        
        const div = document.createElement('div');
        div.className = 'split-part-box';
        div.dataset.part = newPart;
        div.style = "border:1px solid var(--border-color); border-radius:6px;";
        div.innerHTML = `
            <div style="background:#dc2626; color:white; padding:10px; font-weight:bold; display:flex; justify-content:space-between;">
                Part ${newPart} <button class="btn-secondary" style="padding:2px 8px; font-size:0.8rem; color:#dc2626; background:white;" onclick="assignItemsToPart(${newPart})">Add</button>
            </div>
            <div class="part-items" id="part-items-${newPart}" style="padding:10px; min-height:50px; font-size:0.9rem;"></div>
        `;
        container.appendChild(div);
    }

    function submitSplit() {
        const payload = {
            order_id: currentSettleOrderId,
            split_type: currentSplitType,
        };
        
        if (currentSplitType === 'portion') {
            payload.split_ways = parseInt(document.getElementById('split-ways').value);
        } else if (currentSplitType === 'percentage') {
            payload.percentages = [
                parseInt(document.getElementById('split-percentage-1').value),
                parseInt(document.getElementById('split-percentage-2').value)
            ];
        } else if (currentSplitType === 'item') {
            const parts = [];
            document.querySelectorAll('.split-part-box').forEach(box => {
                const partNum = box.dataset.part;
                const items = [];
                box.querySelectorAll('.split-item-row').forEach(row => {
                    items.push({
                        menu_item_id: parseInt(row.dataset.menuid),
                        price: parseFloat(row.dataset.price)
                    });
                });
                if (items.length > 0) parts.push({ part: partNum, items: items });
            });
            payload.item_parts = parts;
        }
        
        fetch('/api/split_bill', {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': 'IjBhMmFmM2RmMjAwNzFjMDgxMjQ2ZmQ1MDFhOTViZmJkY2FhODA3OGMi.aofBeA.T14rSRliXrk07HXNeSg1hop6nxI'},
            body: JSON.stringify(payload)
        }).then(r => r.json()).then(data => {
            if(data.success) {
                location.reload();
            } else {
                alert(data.message || 'Error splitting bill');
            }
        });
    }

    function submitSettle() {
        const method = document.querySelector('input[name="payment-method"]:checked').value;
        const otherMethod = document.getElementById('other-payment-type').value;
        const paymentNote = document.getElementById('payment-note').value;
        const customerPaid = parseFloat(document.getElementById('settle-customer-paid').value) || 0;
        const tipAmount = parseFloat(document.getElementById('settle-tip').value) || 0;
        const coupon = document.getElementById('settle-coupon').value;
        const redeemedPoints = (appliedDiscountType === 'loyalty') ? appliedDiscountValue : 0;
        const delivery = document.getElementById('settle-delivery') ? document.getElementById('settle-delivery').value : 0;
        
        // Calculate change for DB
        const total = parseFloat(document.getElementById('settle-amount').value) || 0;
        let change = 0;
        if (customerPaid > total) {
            change = customerPaid - total;
        }
        
        let payload = {
            order_ids: [currentSettleOrderId],
            payment_method: method,
            custom_payment_method: method === 'other' ? otherMethod : null,
            payment_note: paymentNote,
            customer_paid: customerPaid,
            change_returned: change,
            tip_amount: tipAmount,
            coupon_code: coupon,
            redeemed_points: redeemedPoints,
            delivery_charge: delivery,
            discount_type: appliedDiscountType,
            discount_value: appliedDiscountValue,
            discount_reason: appliedDiscountReason
        };
        
        fetch('/api/settle_bill', {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': 'IjBhMmFmM2RmMjAwNzFjMDgxMjQ2ZmQ1MDFhOTViZmJkY2FhODA3OGMi.aofBeA.T14rSRliXrk07HXNeSg1hop6nxI'},
            body: JSON.stringify(payload)
        }).then(r => r.json()).then(data => {
            if(data.success) {
                location.reload();
            } else {
                alert(data.message || 'Error settling bill');
            }
        });
    }

    // Unlock audio on first user interaction to bypass browser autoplay policies
    let audioUnlocked = false;
    document.body.addEventListener('click', () => {
        if (!audioUnlocked) {
            const audio = document.getElementById('notif-sound');
            if (audio) {
                audio.play().then(() => {
                    audio.pause();
                    audio.currentTime = 0;
                    audioUnlocked = true;
                }).catch(err => console.log('Audio unlock failed', err));
            }
        }
    });
    
    function resolveCall(callId) {
        fetch(`/api/resolve_call/${callId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]') ? document.querySelector('meta[name="csrf-token"]').content : ''}
        }).then(r => r.json()).then(data => {
            if(data.success) {
                const el = document.getElementById(`waiter-call-${callId}`);
                if (el) el.remove();
            }
        });
    }

    let lastUpdateCheck = Date.now() / 1000;
    
    // Check if we need to play a sound from a previous reload
    if (localStorage.getItem('play_update_sound') === 'true') {
        localStorage.removeItem('play_update_sound');
        if (document.getElementById('sound-toggle').checked) {
            const audio = document.getElementById('notif-sound');
            if (audio) {
                let playCount = 0;
                function playBeep() {
                    if (playCount < 3) {
                        audio.play().catch(e => console.log('Audio play failed:', e));
                    }
                }
                audio.onended = () => {
                    playCount++;
                    if (playCount < 3) {
                        setTimeout(playBeep, 500);
                    }
                };
                playBeep();
            }
        }
    }
    
    setInterval(async () => {
        // If a modal is open (e.g. settling bill), delay the update so we don't interrupt the user
        if (document.querySelector('.modal.active')) return;
        
        try {
            const resp = await fetch(`/api/check_updates?since=${lastUpdateCheck}`);
            if (resp.ok) {
                const data = await resp.json();
                if (data.has_updates) {
                    localStorage.setItem('play_update_sound', 'true');
                    try {
                        const htmlResp = await fetch(window.location.href);
                        const htmlText = await htmlResp.text();
                        const doc = new DOMParser().parseFromString(htmlText, 'text/html');
                        document.querySelector('.kanban-board').innerHTML = doc.querySelector('.kanban-board').innerHTML;
                        updateCounts();
                        lastUpdateCheck = data.timestamp;
                    } catch(e) { window.location.reload(); }
                }
            }
        } catch (e) {
            console.error("Polling error", e);
        }
    }, 10000);

    // Drag and Drop Logic
    function allowDrop(ev) {
        ev.preventDefault();
    }

    function drag(ev) {
        ev.dataTransfer.setData("text/plain", ev.target.dataset.id);
        ev.target.classList.add('dragging');
    }

    document.addEventListener('dragend', (ev) => {
        if(ev.target.classList) ev.target.classList.remove('dragging');
    });

    function drop(ev, newStatus) {
        ev.preventDefault();
        const orderId = ev.dataTransfer.getData("text/plain");
        const draggedEl = document.querySelector(`.order-card[data-id="${orderId}"]`);
        
        // Find the closest column body
        let dropTarget = ev.target.closest('.kanban-column').querySelector('.column-body');
        
        if (draggedEl && dropTarget && draggedEl.parentElement !== dropTarget) {
            dropTarget.appendChild(draggedEl);
            updateStatusAPI(orderId, newStatus);
            updateCardButtons(draggedEl, newStatus);
        }
    }
    
    // Button Logic
    function updateStatus(orderId, newStatus) {
        try {
            const card = document.querySelector(`.order-card[data-id="${orderId}"]`);
            const targetList = document.getElementById(`list-${newStatus}`);
            if (card && targetList) {
                targetList.appendChild(card);
                updateStatusAPI(orderId, newStatus);
                updateCardButtons(card, newStatus);
            } else {
                alert('DOM Error: Cannot find card or target list');
            }
        } catch(e) {
            alert('JS Error: ' + e);
        }
    }
    }
    
    function updateCardButtons(card, status) {
        const actionDiv = card.querySelector('.status-btn-container');
        if (!actionDiv) return;
        if (status === 'new') {
            actionDiv.innerHTML = `<button class="btn-status" style="flex:1;" onclick="updateStatus(${card.dataset.id}, 'preparing')">Start Preparing</button>`;
        } else if (status === 'preparing') {
            actionDiv.innerHTML = `<button class="btn-status" style="flex:1;" onclick="updateStatus(${card.dataset.id}, 'served')">Mark Served</button>`;
        } else if (status === 'served') {
            actionDiv.innerHTML = `<button class="btn-status" style="flex:1;" onclick="updateStatus(${card.dataset.id}, 'completed')">Complete</button>`;
        } else {
            actionDiv.innerHTML = '';
        }
        updateCounts();
    }
    
    async function updateStatusAPI(orderId, status) {
        try {
            await fetch('/api/update_order_status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]') ? document.querySelector('meta[name="csrf-token"]').content : '' },
                body: JSON.stringify({ order_id: orderId, status: status })
            });
        } catch (err) {
            console.error("Failed to update status", err);
            alert("Error updating order status!");
        }
    }
    
    function updateCounts() {
        document.getElementById('count-new').innerText = document.querySelectorAll('#list-new .order-card').length;
        document.getElementById('count-preparing').innerText = document.querySelectorAll('#list-preparing .order-card').length;
        document.getElementById('count-served').innerText = document.querySelectorAll('#list-served .order-card').length;
        document.getElementById('count-completed').innerText = document.querySelectorAll('#list-completed .order-card').length;
    }
    
    // Filtering logic
    function applyFilters() {
        const typeFilter = document.getElementById('filter-type').value;
        const branchFilter = document.getElementById('filter-branch').value;
        
        document.querySelectorAll('.order-card').forEach(card => {
            const cardType = card.dataset.type;
            const cardBranch = card.dataset.branch;
            
            let matchType = (typeFilter === 'all' || cardType === typeFilter);
            let matchBranch = (branchFilter === 'all' || cardBranch === branchFilter);
            
            if (matchType && matchBranch) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
        // We do not update counts on filter to show true counts, or we could if requested.
    }
    
    function clearFilters() {
        document.getElementById('filter-type').value = 'all';
        document.getElementById('filter-branch').value = 'all';
        applyFilters();
    }

    // Dynamic timer for Kitchen Display System (KDS)
    function updateOrderTimers() {
        document.querySelectorAll('.order-elapsed').forEach(timer => {
            const timeStr = timer.getAttribute('data-time');
            if (timeStr) {
                // Parse timestamp directly
                const orderTime = parseFloat(timeStr);
                const now = new Date().getTime();
                const diffMins = Math.floor(Math.max(0, now - orderTime) / 60000);
                
                timer.innerText = diffMins + 'm ago';
                
                // Color coding
                if (diffMins >= 20) {
                    timer.style.background = '#fef2f2'; // light red
                    timer.style.color = '#dc2626'; // dark red
                } else if (diffMins >= 10) {
                    timer.style.background = '#fffbeb'; // light orange
                    timer.style.color = '#d97706'; // dark orange
                } else {
                    timer.style.background = '#f0fdf4'; // light green
                    timer.style.color = '#16a34a'; // dark green
                }
            }
        });
    }
    
    // Initial run and then every 30 seconds
    updateOrderTimers();
    setInterval(updateOrderTimers, 30000);
