import re

with open('templates/admin/live_orders.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. updateStatusAPI
old_func4 = '''    async function updateStatusAPI(orderId, status) {
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
    }'''

new_func4 = '''    function updateStatusAPI(orderId, status) {
        fetch('/api/update_order_status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]') ? document.querySelector('meta[name="csrf-token"]').content : '' },
            body: JSON.stringify({ order_id: orderId, status: status })
        }).catch(function(err) {
            console.error("Failed to update status", err);
            alert("Error updating order status!");
        });
    }'''
html = html.replace(old_func4, new_func4)

# 2. openSplitModal
old_func2 = '''    async function openSplitModal() {
        const settleModal = document.getElementById('settle-modal');
        settleModal.style.display = 'none';
        
        try {
            const resp = await fetch(/api/order_details/\);
            const data = await resp.json();
            
            const list = document.getElementById('split-items-list');
            list.innerHTML = '';
            
            if (data.success && data.items) {
                data.items.forEach(item => {
                    splitItemCounter++;
                    list.innerHTML += \
                        <div class="split-item-row" data-id="\" data-menuid="\" data-price="\" style="display:flex; gap:10px; padding:8px 0; border-bottom:1px solid var(--border-color);">
                            <input type="checkbox" class="split-item-chk" value="\">
                            <span>\</span>
                            <span style="margin-left:auto;">?\</span>
                            <input type="number" class="split-item-qty" value="\" min="1" max="\" style="width:60px; padding:4px;">
                        </div>
                    \;
                });
            }
        } catch(e) {
            alert('Failed to load order items for splitting.');
            console.error(e);
        }
        
        document.getElementById('split-modal').style.display = 'flex';
        updateSplitTotal();
    }'''

new_func2 = '''    function openSplitModal() {
        const settleModal = document.getElementById('settle-modal');
        settleModal.style.display = 'none';
        
        fetch(/api/order_details/\)
            .then(function(resp) { return resp.json(); })
            .then(function(data) {
                const list = document.getElementById('split-items-list');
                list.innerHTML = '';
                
                if (data.success && data.items) {
                    data.items.forEach(item => {
                        splitItemCounter++;
                        list.innerHTML += \
                            <div class="split-item-row" data-id="\" data-menuid="\" data-price="\" style="display:flex; gap:10px; padding:8px 0; border-bottom:1px solid var(--border-color);">
                                <input type="checkbox" class="split-item-chk" value="\">
                                <span>\</span>
                                <span style="margin-left:auto;">?\</span>
                                <input type="number" class="split-item-qty" value="\" min="1" max="\" style="width:60px; padding:4px;">
                            </div>
                        \;
                    });
                }
                document.getElementById('split-modal').style.display = 'flex';
                updateSplitTotal();
            })
            .catch(function(e) {
                alert('Failed to load order items for splitting.');
                console.error(e);
            });
    }'''
html = html.replace(old_func2, new_func2)

# 3. openSettleModal
old_func1 = '''    async function openSettleModal(orderId, type, customerName, customerMobile, totalStr, coupon) {
        currentSettleOrderId = orderId;
        currentSettleOrder = type;
        currentSettleMobile = customerMobile;
        document.getElementById('settle-total').textContent = totalStr;
        document.getElementById('settle-final').textContent = totalStr;
        document.getElementById('settle-discount').value = '';
        
        let infoHtml = <p><strong>Order #</strong> ()</p>;
        if (customerName) infoHtml += <p>Customer: </p>;
        if (customerMobile) infoHtml += <p>Mobile: </p>;
        if (coupon) infoHtml += <p style="color:var(--brand-orange);">Coupon: </p>;
        
        // Fetch past orders if mobile exists
        if (currentSettleMobile && currentSettleMobile.length >= 10) {
            try {
                const resp = await fetch('/api/customer/history?mobile=' + encodeURIComponent(currentSettleMobile));
                const data = await resp.json();
                if (data.success && data.count > 0) {
                    infoHtml += <div style="margin-top:10px; padding:10px; background:#fef3c7; border-radius:6px; font-size:0.9rem;">
                        <i class="fa-solid fa-clock-rotate-left"></i> Past Orders: <strong></strong><br>
                        Total Spent: ?<br>
                        <a href="#" onclick="showHistoryModal('')" style="color:#b45309; text-decoration:underline;">View Details</a>
                    </div>;
                }
            } catch(e) {
                console.error("Failed to fetch history", e);
            }
        }
        
        document.getElementById('settle-info').innerHTML = infoHtml;
        document.getElementById('settle-modal').style.display = 'flex';
    }'''

new_func1 = '''    function openSettleModal(orderId, type, customerName, customerMobile, totalStr, coupon) {
        currentSettleOrderId = orderId;
        currentSettleOrder = type;
        currentSettleMobile = customerMobile;
        document.getElementById('settle-total').textContent = totalStr;
        document.getElementById('settle-final').textContent = totalStr;
        document.getElementById('settle-discount').value = '';
        
        let infoHtml = <p><strong>Order #</strong> ()</p>;
        if (customerName) infoHtml += <p>Customer: </p>;
        if (customerMobile) infoHtml += <p>Mobile: </p>;
        if (coupon) infoHtml += <p style="color:var(--brand-orange);">Coupon: </p>;
        
        // Fetch past orders if mobile exists
        if (currentSettleMobile && currentSettleMobile.length >= 10) {
            fetch('/api/customer/history?mobile=' + encodeURIComponent(currentSettleMobile))
                .then(function(resp) { return resp.json(); })
                .then(function(data) {
                    if (data.success && data.count > 0) {
                        infoHtml += <div style="margin-top:10px; padding:10px; background:#fef3c7; border-radius:6px; font-size:0.9rem;">
                            <i class="fa-solid fa-clock-rotate-left"></i> Past Orders: <strong></strong><br>
                            Total Spent: ?<br>
                            <a href="#" onclick="showHistoryModal('')" style="color:#b45309; text-decoration:underline;">View Details</a>
                        </div>;
                        document.getElementById('settle-info').innerHTML = infoHtml;
                    }
                })
                .catch(function(e) {
                    console.error("Failed to fetch history", e);
                });
        }
        
        document.getElementById('settle-info').innerHTML = infoHtml;
        document.getElementById('settle-modal').style.display = 'flex';
    }'''
html = html.replace(old_func1, new_func1)


# 4. setInterval
old_func3 = '''    setInterval(async () => {
        if (!document.hidden) {
            try {
                const resp = await fetch(/api/check_updates?since=\);
                if (resp.ok) {
                    const data = await resp.json();
                    if (data.has_updates) {
                        lastUpdateCheck = data.timestamp;
                        const htmlResp = await fetch(window.location.href);
                        const htmlText = await htmlResp.text();
                        
                        // Parse new HTML and replace columns
                        const parser = new DOMParser();
                        const newDoc = parser.parseFromString(htmlText, 'text/html');
                        
                        ['new', 'preparing', 'served', 'completed'].forEach(status => {
                            const oldList = document.getElementById(list-\);
                            const newList = newDoc.getElementById(list-\);
                            if (oldList && newList) {
                                oldList.innerHTML = newList.innerHTML;
                            }
                        });
                        updateCounts();
                    }
                }
            } catch(e) { console.error('Auto-refresh failed:', e); }
        }
    }, 30000);'''

new_func3 = '''    setInterval(function() {
        if (!document.hidden) {
            fetch(/api/check_updates?since=\)
                .then(function(resp) {
                    if (resp.ok) return resp.json();
                    throw new Error('Not ok');
                })
                .then(function(data) {
                    if (data && data.has_updates) {
                        lastUpdateCheck = data.timestamp;
                        return fetch(window.location.href).then(function(r) { return r.text(); });
                    }
                    return null;
                })
                .then(function(htmlText) {
                    if (htmlText) {
                        const parser = new DOMParser();
                        const newDoc = parser.parseFromString(htmlText, 'text/html');
                        ['new', 'preparing', 'served', 'completed'].forEach(status => {
                            const oldList = document.getElementById(list-\);
                            const newList = newDoc.getElementById(list-\);
                            if (oldList && newList) {
                                oldList.innerHTML = newList.innerHTML;
                            }
                        });
                        updateCounts();
                    }
                })
                .catch(function(e) { console.error('Auto-refresh failed:', e); });
        }
    }, 30000);'''
html = html.replace(old_func3, new_func3)

with open('templates/admin/live_orders.html', 'w', encoding='utf-8') as f:
    f.write(html)
