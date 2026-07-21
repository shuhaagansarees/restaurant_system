let cart = {};

// Tabs Logic
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.menu-section').forEach(s => s.classList.remove('active'));
        
        tab.classList.add('active');
        document.getElementById(tab.dataset.target).classList.add('active');
    });
});

function getVariant(itemId) {
    const radio = document.querySelector(`input[name="var_${itemId}"]:checked`);
    return radio ? radio.value : null;
}

function addToCart(btn) {
    const menuItem = btn.closest('.menu-item');
    const id = menuItem.dataset.id;
    
    btn.style.display = 'none';
    menuItem.querySelector('.stepper').classList.add('active');
    
    updateQty(menuItem.querySelector('.stepper button'), 1, true);
}

function updateQty(btn, change, fromAdd = false) {
    const menuItem = btn.closest('.menu-item');
    const id = menuItem.dataset.id;
    const name = menuItem.dataset.name;
    const price = parseFloat(menuItem.dataset.price);
    const variant = getVariant(id);
    
    // Unique key if variants matter, simplified here by ID
    const cartKey = id; 

    if (!cart[cartKey]) {
        cart[cartKey] = { id: id, name: name, price: price, quantity: 0, variant: variant };
    }
    
    if (!fromAdd) {
        cart[cartKey].quantity += change;
    } else {
        cart[cartKey].quantity = 1;
    }
    
    const qtySpan = menuItem.querySelector('.qty');
    
    if (cart[cartKey].quantity <= 0) {
        delete cart[cartKey];
        menuItem.querySelector('.stepper').classList.remove('active');
        menuItem.querySelector('.btn-add').style.display = 'block';
        qtySpan.innerText = "1"; // reset for next time
    } else {
        qtySpan.innerText = cart[cartKey].quantity;
    }
    
    updateCartUI();
}

function updateCartUI() {
    let totalItems = 0;
    let totalPrice = 0;
    
    for (let key in cart) {
        totalItems += cart[key].quantity;
        totalPrice += cart[key].quantity * cart[key].price;
    }
    
    const stickyCart = document.getElementById('sticky-cart');
    document.getElementById('cart-count').innerText = totalItems;
    document.getElementById('cart-total').innerText = totalPrice;
    
    if (totalItems > 0) {
        stickyCart.classList.add('active');
    } else {
        stickyCart.classList.remove('active');
    }
}

let appliedCoupon = null;
let appliedDiscount = 0;

async function applyCoupon() {
    const code = document.getElementById('coupon-code').value;
    const msgEl = document.getElementById('coupon-message');
    if (!code) {
        msgEl.innerText = 'Please enter a coupon code.';
        msgEl.style.color = 'var(--danger-color)';
        return;
    }
    
    // Calculate total price
    let totalPrice = 0;
    for (let key in cart) {
        totalPrice += cart[key].quantity * cart[key].price;
    }
    
    msgEl.innerText = 'Applying...';
    msgEl.style.color = 'var(--text-secondary)';
    
    try {
        const response = await fetch('/api/verify_coupon', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code, total: totalPrice })
        });
        const data = await response.json();
        
        if (data.success) {
            appliedCoupon = data.code;
            appliedDiscount = data.discount;
            msgEl.innerText = `${data.message} Discount: ₹${data.discount}`;
            msgEl.style.color = 'var(--success-color)';
            // update checkout total view
            openCheckout();
        } else {
            appliedCoupon = null;
            appliedDiscount = 0;
            msgEl.innerText = data.message;
            msgEl.style.color = 'var(--danger-color)';
            openCheckout();
        }
    } catch (err) {
        msgEl.innerText = 'Failed to verify coupon.';
        msgEl.style.color = 'var(--danger-color)';
    }
}

function openCheckout() {
    const reviewDiv = document.getElementById('cart-review');
    reviewDiv.innerHTML = '';
    let totalPrice = 0;
    for(let key in cart) {
        const item = cart[key];
        totalPrice += item.price * item.quantity;
        let varText = item.variant ? ` (${item.variant})` : '';
        reviewDiv.innerHTML += `<div style="display:flex; justify-content:space-between; margin-bottom:5px;">
            <span>${item.quantity}x ${item.name}${varText}</span>
            <span>₹${item.price * item.quantity}</span>
        </div>`;
    }
    
    if (appliedCoupon && appliedDiscount > 0) {
        reviewDiv.innerHTML += `<div style="display:flex; justify-content:space-between; margin-bottom:5px; color: var(--success-color); font-weight: bold;">
            <span>Coupon (${appliedCoupon})</span>
            <span>- ₹${appliedDiscount}</span>
        </div>`;
        totalPrice -= appliedDiscount;
        if (totalPrice < 0) totalPrice = 0;
    }
    
    reviewDiv.innerHTML += `<div style="display:flex; justify-content:space-between; margin-top:10px; padding-top:10px; border-top: 1px solid var(--border-color); font-weight:bold;">
        <span>Total</span>
        <span>₹${totalPrice}</span>
    </div>`;
    
    document.getElementById('checkout-modal').classList.add('active');
}

function closeCheckout() {
    document.getElementById('checkout-modal').classList.remove('active');
}

async function placeOrder() {
    let finalTable = currentTable;
    let manualTableEl = document.getElementById('manual-table');
    let orderType = 'dine-in';
    
    if (!finalTable && manualTableEl) {
        finalTable = manualTableEl.value;
        if (!finalTable) {
            orderType = 'parcel';
        }
    }
    
    const custName = document.getElementById('cust-name').value;
    const custMobile = document.getElementById('cust-mobile').value;
    
    const items = Object.values(cart);
    
    const payload = {
        table_name: finalTable,
        order_type: orderType,
        customer_name: custName,
        customer_mobile: custMobile,
        coupon_code: appliedCoupon,
        items: items
    };
    
    try {
        const response = await fetch('/api/place_order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]') ? document.querySelector('meta[name="csrf-token"]').content : '' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        
        if (data.success) {
            const beep = new Audio('/static/audio/beep.wav');
            beep.play().catch(e => console.log(e));
            setTimeout(() => {
                window.location.href = `/order/${data.order_id}`;
            }, 250); // wait for beep to finish before redirecting
        } else {
            alert('Error: ' + data.message);
        }
    } catch (err) {
        console.error(err);
        alert('Failed to place order.');
    }
}
