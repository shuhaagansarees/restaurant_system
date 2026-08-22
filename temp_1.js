
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

    function openSettleModal(orderId, type, customerName, customerMobile, totalStr, coupon) {
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
            fetch('/api/customer/history?mobile=' + encodeURIComponent(currentSettleMobile))
                .then(function(resp) { return resp.json(); })
                .then(function(data) {
                    if (data.success && data.loyalty_points > 0) {
                        currentAvailablePoints = data.loyalty_points;
                        document.getElementById('settle-available-points').innerText = data.loyalty_points;
                        document.getElementById('settle-redeem-points').max = data.loyalty_points;
                        document.getElementById('settle-loyalty-section').style.display = 'block';
                    }
                })
                .catch(function(e) { console.error('Error fetching loyalty points:', e); });
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
    
    function openSplitModal() {
        document.getElementById('split-modal').classList.add('active');
        fetch(`/api/order_details/${currentSettleOrderId}`)
            .then(function(resp) { return resp.json(); })
            .then(function(data) {
                if (data.success) {
                    renderSplitItems(data.items);
                }
            })
            .catch(function(e) {
                console.error(e);
            });
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
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': '{{ csrf_token() }}'},
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
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': '{{ csrf_token() }}'},
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
    
    setInterval(function() {
        // If a modal is open (e.g. settling bill), delay the update so we don't interrupt the user
        if (document.querySelector('.modal.active')) return;
        
        fetch(`/api/check_updates?since=${lastUpdateCheck}`)
            .then(function(resp) { return resp.ok ? resp.json() : null; })
            .then(function(data) {
                if (data && data.has_updates) {
                    localStorage.setItem('play_update_sound', 'true');
                    fetch(window.location.href)
                        .then(function(htmlResp) { return htmlResp.text(); })
                        .then(function(htmlText) {
                            const doc = new DOMParser().parseFromString(htmlText, 'text/html');
                            document.querySelector('.kanban-board').innerHTML = doc.querySelector('.kanban-board').innerHTML;
                            updateCounts();
                            lastUpdateCheck = data.timestamp;
                        })
                        .catch(function(e) { window.location.reload(); });
                }
            })
            .catch(function(e) {
                console.error("Polling error", e);
            });
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
