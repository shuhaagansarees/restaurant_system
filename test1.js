
    function switchCategory(catId, btnEl) {
        document.querySelectorAll('.category-tab-btn').forEach(btn => btn.classList.remove('active'));
        btnEl.classList.add('active');
        
        if (window.innerWidth <= 768) {
            document.querySelectorAll('.category-section').forEach(sec => sec.classList.remove('active'));
            const target = document.getElementById(catId);
            if (target) target.classList.add('active');
        } else {
            const target = document.getElementById(catId);
            if (target) {
                const offset = 80;
                const bodyRect = document.body.getBoundingClientRect().top;
                const elementRect = target.getBoundingClientRect().top;
                const elementPosition = elementRect - bodyRect;
                const offsetPosition = elementPosition - offset;
                window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
            }
        }
    }
    
    function toggleMobileCart() {
        document.querySelector('.col-cart').classList.toggle('active');
        const btn = document.querySelector('.cart-toggle-btn');
        if(document.querySelector('.col-cart').classList.contains('active')){
            btn.innerText = 'Close Cart';
        } else {
            btn.innerText = 'View Cart';
        }
    }

    let cart = {};
    
    // Initialize cart with existing order items
    {% for item in order.items %}
    if (!cart[{{ item.menu_item_id }}]) {
        cart[{{ item.menu_item_id }}] = { 
            name: '{{ item.menu_item.name|replace("'", "\\'") }}', 
            price: {{ item.price_at_order }}, 
            qty: 0,
            original_kots: {}
        };
    }
    cart[{{ item.menu_item_id }}].qty += {{ item.quantity }};
    cart[{{ item.menu_item_id }}].original_kots[{{ item.kot_number }}] = (cart[{{ item.menu_item_id }}].original_kots[{{ item.kot_number }}] || 0) + {{ item.quantity }};
    {% endfor %}
    
    document.addEventListener('DOMContentLoaded', () => {
        // Populate existing quantities in the DOM
        for (let itemId in cart) {
            document.querySelectorAll('.qty-display-' + itemId).forEach(el => el.innerText = cart[itemId].qty);
            document.querySelectorAll('.card-item-' + itemId).forEach(el => el.classList.add('active-in-cart'));
        }
        renderCart();
    });
    
    
    function updateCartEvent(element, delta) {
        const card = element.closest('.menu-item-card');
        if (!card) return;
        const itemId = card.dataset.id;
        const name = card.dataset.name;
        const price = parseFloat(card.dataset.price);
        updateCart(itemId, name, price, delta);
    }
    function updateCart(itemId, name, price, delta) {
        if (!cart[itemId]) {
            cart[itemId] = { name: name, price: price, qty: 0, original_kots: {} };
        }
        
        cart[itemId].qty += delta;
        
        if (cart[itemId].qty <= 0) {
            delete cart[itemId];
            document.querySelectorAll('.qty-display-' + itemId).forEach(el => el.innerText = '0');
            document.querySelectorAll('.card-item-' + itemId).forEach(el => el.classList.remove('active-in-cart'));
        } else {
            document.querySelectorAll('.qty-display-' + itemId).forEach(el => el.innerText = cart[itemId].qty);
            document.querySelectorAll('.card-item-' + itemId).forEach(el => el.classList.add('active-in-cart'));
        }
        
        renderCart();
    }
    
    function renderCart() {
        const cartDiv = document.getElementById('cart-items');
        let html = '';
        let total = 0;
        
        const keys = Object.keys(cart);
        if (keys.length === 0) {
            cartDiv.innerHTML = '<div style="color: var(--text-secondary); text-align: center; margin-top: 20px;">Cart is empty (Order will be cancelled if saved)</div>';
            document.getElementById('cart-total-amt').innerText = '₹0';
            const mcCount = document.getElementById('mobile-cart-count');
            if (mcCount) {
                mcCount.innerText = '0';
                document.getElementById('mobile-cart-total').innerText = '₹0';
            }
            return { newItems: [] };
        }
        
        // Group items by KOT
        const kotGroups = {};
        const newItems = [];
        
        keys.forEach(id => {
            const item = cart[id];
            total += item.qty * item.price;
            
            // Distribute qty across original_kots, and put the rest in newItems
            let remainingQty = item.qty;
            
            // We iterate through original_kots in descending order (highest KOT first)
            // wait, if we are reducing, we should reduce from highest KOT first to match backend.
            const sortedKots = Object.keys(item.original_kots).map(Number).sort((a,b) => b - a);
            
            // Actually, we want to build what is left.
            // Backend removes from highest KOT.
            // So we fill from lowest KOT up to remainingQty.
            const ascKots = [...sortedKots].sort((a,b) => a - b);
            
            for (let kot of ascKots) {
                let originalQty = item.original_kots[kot];
                if (remainingQty > 0) {
                    let take = Math.min(originalQty, remainingQty);
                    if (!kotGroups[kot]) kotGroups[kot] = [];
                    kotGroups[kot].push({ name: item.name, price: item.price, qty: take });
                    remainingQty -= take;
                }
            }
            
            // If there's still remainingQty, it's a new addition!
            if (remainingQty > 0) {
                newItems.push({ name: item.name, price: item.price, qty: remainingQty });
            }
        });
        
        // Render KOTs
        const sortedGroupKeys = Object.keys(kotGroups).map(Number).sort((a,b) => a - b);
        sortedGroupKeys.forEach(kot => {
            html += `<div style="background: #f8fafc; padding: 10px; margin-bottom: 10px; border-radius: 6px; border: 1px solid var(--border-color);">
                        <h4 style="margin: 0 0 10px 0; color: var(--text-secondary); font-size: 0.85rem; text-transform: uppercase;">KOT - ${kot}</h4>`;
            kotGroups[kot].forEach(i => {
                html += `<div class="cart-item" style="margin-bottom: 5px; padding-bottom: 0; border: none;">
                            <div>${i.name} <span style="color: var(--text-secondary)">x${i.qty}</span></div>
                            <div style="font-weight: 500;">₹${i.qty * i.price}</div>
                        </div>`;
            });
            html += `</div>`;
        });
        
        // Render New Additions
        if (newItems.length > 0) {
            html += `<div style="background: #fffaf5; padding: 10px; margin-bottom: 10px; border-radius: 6px; border: 1px dashed var(--brand-orange);">
                        <h4 style="margin: 0 0 10px 0; color: var(--brand-orange); font-size: 0.85rem; text-transform: uppercase;">⭐ New Additions (Next KOT)</h4>`;
            newItems.forEach(i => {
                html += `<div class="cart-item" style="margin-bottom: 5px; padding-bottom: 0; border: none;">
                            <div>${i.name} <span style="color: var(--text-secondary)">x${i.qty}</span></div>
                            <div style="font-weight: 500;">₹${i.qty * i.price}</div>
                        </div>`;
            });
            html += `</div>`;
        }
        
        cartDiv.innerHTML = html;
        document.getElementById('cart-total-amt').innerText = '₹' + total;
        
        let itemCount = 0;
        keys.forEach(id => itemCount += cart[id].qty);
        const mcCount = document.getElementById('mobile-cart-count');
        if (mcCount) {
            mcCount.innerText = itemCount;
            document.getElementById('mobile-cart-total').innerText = '₹' + total;
        }
        
        return { newItems };
    }
    
    function searchMenu() {
        const input = document.getElementById('searchInput').value.toLowerCase();
        document.querySelectorAll('.search-target').forEach(card => {
            const name = card.querySelector('.item-name').innerText.toLowerCase();
            const code = card.dataset.code || '';
            card.style.display = (name.includes(input) || code.includes(input)) ? 'flex' : 'none';
        });
    }
    
    async function saveOrder(printKOT = false) {
        const keys = Object.keys(cart);
        if (keys.length === 0) {
            if (!confirm('Cart is empty! Saving this will CANCEL the entire order. Continue?')) {
                return;
            }
        }
        
        const btn = document.getElementById('btnSaveOrder');
        const btnPrint = document.getElementById('btnSavePrintOrder');
        btn.disabled = true;
        btnPrint.disabled = true;
        if(printKOT) {
            btnPrint.innerText = 'Saving...';
        } else {
            btn.innerText = 'Saving...';
        }
        
        const items = keys.map(id => ({
            id: parseInt(id),
            quantity: cart[id].qty,
            price: cart[id].price
        }));
        
        const coversInput = document.getElementById('order-covers');
        const custMobileInput = document.getElementById('order-custMobile');
        const custNameInput = document.getElementById('order-custName');
        const payload = {
            order_id: {{ order.id }},
            items: items,
            covers: coversInput ? coversInput.value : 1,
            customer_mobile: custMobileInput ? custMobileInput.value.trim() : null,
            customer_name: custNameInput ? custNameInput.value.trim() : null
        };
        
        try {
            const resp = await fetch('/api/update_order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]') ? document.querySelector('meta[name="csrf-token"]').content : '' },
                body: JSON.stringify(payload)
            });
            
            if (resp.ok) {
                if(printKOT) {
                    window.open('/admin/kot/print/{{ order.id }}', '_blank');
                }
                window.location.href = '/admin/live_orders';
            } else {
                const data = await resp.json();
                alert('Failed to save order: ' + (data.error || 'Unknown error'));
                btn.disabled = false;
                btnPrint.disabled = false;
                btn.innerText = 'Save Changes';
                btnPrint.innerText = 'Save & Print KOT';
            }
        } catch (e) {
            console.error(e);
            alert('Network error');
            btn.disabled = false;
            btnPrint.disabled = false;
            btn.innerText = 'Save Changes';
            btnPrint.innerText = 'Save & Print KOT';
        }
    }
