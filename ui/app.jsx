const API = '';
const {useState, useEffect, useRef} = React;

/* ── SVG Hex Logo ── */
const HexLogo = ({size=64}) => (
  <svg width={size} height={size} viewBox="0 0 100 100">
    <polygon points="50,2 93,27 93,73 50,98 7,73 7,27" fill="none" stroke="#F0B90B" strokeWidth="3"/>
    <text x="50" y="58" textAnchor="middle" fontFamily="Orbitron" fontWeight="700" fontSize="38" fill="#F0B90B">Q</text>
  </svg>
);

/* ── API ── */
const api = {
  price: (s='BTCUSDT') => fetch(`${API}/api/price?symbol=${s}`).then(r=>r.json()),
  balance: () => fetch(`${API}/api/balance`).then(r=>r.json()),
  orders: () => fetch(`${API}/api/orders`).then(r=>r.json()),
  placeOrder: (body) => fetch(`${API}/api/order`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(r=>{if(!r.ok) return r.json().then(e=>{throw new Error(e.detail||'Order failed')});return r.json()})
};

/* ── TOUR CONFIG ── */
const TOUR_STEPS = [
  {id:'price',  target:'#tour-price',   title:'Live Price Ticker',      body:'Live BTCUSDT price updates every 3 seconds. Green = up, Red = down.'},
  {id:'sidebar',target:'#tour-sidebar', title:'Navigation Sidebar',     body:'Navigate between Terminal, Portfolio, Strategies and Signals.'},
  {id:'form',   target:'#tour-form',    title:'Place Order',            body:'Select order type, enter quantity and price to open a position.'},
  {id:'sides',  target:'#tour-sides',   title:'BUY / SELL',             body:'Execute long or short positions instantly with one click.'},
  {id:'activity',target:'#tour-activity',title:'Recent Activity',       body:'Real-time order execution log — updates every 3 seconds.'},
  {id:'balance',target:'#tour-balance', title:'Margin Balance',         body:'Your live margin balance pulled directly from Binance.'},
  {id:'done',   target:null,            title:"You're ready to trade",  body:'Precision Trading, Redefined.'},
];

/* ── ONBOARDING TOUR ── */
function Tour({onDone}) {
  const [step, setStep] = useState(0);
  const [pos, setPos] = useState(null);
  const cur = TOUR_STEPS[step];
  const isLast = step === TOUR_STEPS.length - 1;

  useEffect(() => {
    if (!cur.target) { setPos(null); return; }
    const el = document.querySelector(cur.target);
    if (!el) { setPos(null); return; }
    const r = el.getBoundingClientRect();
    setPos({top: r.top + window.scrollY, left: r.left + window.scrollX, width: r.width, height: r.height});
  }, [step]);

  const next = () => { if (isLast) onDone(); else setStep(s => s+1); };
  const skip = () => onDone();

  const PAD = 10;
  return (
    <div className="tour-overlay">
      {pos && (
        <div className="tour-spotlight" style={{top:pos.top-PAD, left:pos.left-PAD, width:pos.width+PAD*2, height:pos.height+PAD*2}}/>
      )}
      <div className={`tour-card ${!pos?'tour-card-center':''}`} style={pos ? {top: Math.min(pos.top+pos.height+PAD+16, window.innerHeight-220), left: Math.max(8, Math.min(pos.left, window.innerWidth-360))} : {}}>
        {!isLast && <div className="tour-arrow-up">▲</div>}
        <div className="tour-step-count">{step+1} / {TOUR_STEPS.length}</div>
        <div className="tour-title">{cur.title}</div>
        <div className="tour-body">{cur.body}</div>
        {isLast
          ? <button className="btn-enter-terminal" onClick={onDone}>ENTER TERMINAL</button>
          : <div className="tour-actions">
              <button className="btn-tour-next" onClick={next}>NEXT →</button>
              <button className="btn-tour-skip" onClick={skip}>SKIP TOUR</button>
            </div>
        }
      </div>
    </div>
  );
}

/* ── STARTUP ── */
function StartupScreen({onStart}) {
  return (
    <div className="startup">
      <div className="hex-logo"><div className="ring"></div><HexLogo size={64}/></div>
      <div className="brand-name">QUANTRA</div>
      <div className="tagline">Precision Trading, Redefined</div>
      <div className="mode-cards">
        <div className="mode-card" onClick={()=>onStart('dashboard')}>
          <span className="icon">⬡</span>
          <h3>Dashboard View</h3>
          <p>All panels visible at once</p>
          <button className="btn-init" onClick={e=>{e.stopPropagation();onStart('dashboard')}}>INITIALIZE</button>
        </div>
        <div className="mode-card" onClick={()=>onStart('tabbed')}>
          <span className="icon">☰</span>
          <h3>Tabbed View</h3>
          <p>Navigate between sections</p>
          <button className="btn-init" onClick={e=>{e.stopPropagation();onStart('tabbed')}}>INITIALIZE</button>
        </div>
      </div>
      <div className="startup-hint">
        <span className="blink-arrow">▲</span>
        <span className="hint-text">Select your workspace to begin</span>
      </div>
      <div className="status-bar">
        <span><span className="dot"></span>CORE_STABLE</span>
        <span>LATENCY: 12ms</span>
        <span>BUILD: v1.4.2-neon</span>
        <span>PROTOCOL: REST/HMAC-SHA256</span>
      </div>
    </div>
  );
}

/* ── ORDER FORM ── */
function OrderForm({onSubmit, lastPrice}) {
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [type, setType] = useState('LIMIT');
  const [side, setSide] = useState('BUY');
  const [qty, setQty] = useState('0.001');
  const [price, setPrice] = useState('');
  const pctSet = p => setQty((0.01*p).toFixed(4));
  useEffect(()=>{if(lastPrice&&!price) setPrice(parseFloat(lastPrice).toFixed(2))},[lastPrice]);
  const handleSubmit = () => {
    const body = {symbol, side, type, quantity: parseFloat(qty)};
    if(type==='LIMIT') body.price = parseFloat(price);
    onSubmit(body);
  };
  const est = parseFloat(qty||0)*parseFloat(price||lastPrice||0);
  return (
    <div className="panel" id="tour-form">
      <div className="panel-header">⚡ Place Order</div>
      <div className="form-group">
        <label className="form-label">Asset Pair</label>
        <select className="form-select" value={symbol} onChange={e=>setSymbol(e.target.value)}>
          <option>BTCUSDT</option><option>ETHUSDT</option><option>BNBUSDT</option><option>SOLUSDT</option>
        </select>
      </div>
      <div className="order-tabs">
        {['LIMIT','MARKET'].map(t=><button key={t} className={`order-tab ${type===t?'active':''}`} onClick={()=>setType(t)}>{t}</button>)}
      </div>
      {type==='LIMIT'&&<div className="form-group">
        <label className="form-label">Price (USDT)</label>
        <input className="form-input" type="number" step="0.01" value={price} onChange={e=>setPrice(e.target.value)} placeholder="0.00"/>
      </div>}
      <div className="form-group">
        <label className="form-label">Quantity (BTC)</label>
        <input className="form-input" type="number" step="0.001" value={qty} onChange={e=>setQty(e.target.value)}/>
      </div>
      <div className="pct-btns">
        {[25,50,75,100].map(p=><button key={p} className="pct-btn" onClick={()=>pctSet(p)}>{p}%</button>)}
      </div>
      <div className="side-btns" id="tour-sides">
        <button className="btn-buy" onClick={()=>setSide('BUY')} style={side==='BUY'?{}:{opacity:.4}}>BUY / LONG</button>
        <button className="btn-sell" onClick={()=>setSide('SELL')} style={side==='SELL'?{}:{opacity:.4}}>SELL / SHORT</button>
      </div>
      <div className="est-row"><span>EST. MARGIN</span><span>{est?est.toFixed(2):'0.00'} USDT</span></div>
      <div className="est-row"><span>TRADING FEE</span><span>{(est*0.0004).toFixed(4)} USDT</span></div>
      <button className="btn-execute" onClick={handleSubmit}>INITIALIZE ORDER</button>
    </div>
  );
}

/* ── CONFIRM MODAL ── */
function ConfirmModal({order, onConfirm, onCancel, loading}) {
  if(!order) return null;
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal" onClick={e=>e.stopPropagation()}>
        <h3>CONFIRM ORDER</h3>
        {[['Symbol',order.symbol],['Side',order.side],['Type',order.type],['Quantity',order.quantity],['Price',order.price||'MARKET']].map(([l,v])=>
          <div key={l} className="summary-row"><span className="lbl">{l}</span><span className="val">{v}</span></div>
        )}
        <div className="modal-actions">
          {loading?<div className="spinner"></div>:<>
            <button className="btn-confirm" onClick={onConfirm}>CONFIRM</button>
            <button className="btn-cancel" onClick={onCancel}>CANCEL</button>
          </>}
        </div>
      </div>
    </div>
  );
}

/* ── SETTINGS MODAL ── */
function SettingsModal({onClose, onSwitchLayout}) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e=>e.stopPropagation()}>
        <h3>SETTINGS</h3>
        <p style={{color:'var(--secondary)',fontFamily:'var(--font-head)',fontSize:13,marginBottom:16}}>Session configuration</p>
        <button className="btn-confirm" style={{width:'100%'}} onClick={onSwitchLayout}>Switch Layout</button>
        <div className="modal-actions" style={{marginTop:10}}>
          <button className="btn-cancel" style={{flex:1}} onClick={onClose}>CLOSE</button>
        </div>
      </div>
    </div>
  );
}

/* ── CENTER PANEL ── */
function CenterPanel({lastOrder, orders}) {
  return (
    <div style={{display:'flex',flexDirection:'column',gap:12}}>
      <div className="panel">
        <div className="panel-header">📊 Last Order Executed</div>
        {lastOrder ? (
          <div className="last-order">
            <div className="lo-header">✓ ORDER FILLED</div>
            {[['Order ID',lastOrder.orderId],['Status',lastOrder.status],['Executed Qty',lastOrder.executedQty],['Avg Price',lastOrder.avgPrice],['Symbol',lastOrder.symbol],['Side',lastOrder.side]].map(([l,v])=>
              <div key={l} className="lo-row"><span className="label">{l}</span><span className="value">{String(v)}</span></div>
            )}
          </div>
        ) : <div className="empty-state">No orders executed yet</div>}
      </div>
      <div className="panel" id="tour-activity">
        <div className="panel-header">🔔 Recent Activity</div>
        {orders.length===0 && <div className="empty-state">Waiting for signals...</div>}
        {orders.slice(0,6).map((o,i)=>(
          <div key={i} className={`activity-item ${o.side==='BUY'?'buy':'sell'}`}>
            <span className="time">{o.timestamp?new Date(o.timestamp).toLocaleTimeString():'--:--'}</span>
            <span className={`tag ${o.side==='BUY'?'tag-buy':'tag-sell'}`}>{o.side}</span>
            <span className="detail">{o.symbol} {o.type} × {o.quantity}</span>
            <span className={`badge ${o.status==='FILLED'?'badge-filled':o.status==='NEW'?'badge-new':''}`}>{o.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── RIGHT PANEL ── */
function RightPanel({balance, orders}) {
  return (
    <div style={{display:'flex',flexDirection:'column',gap:12}}>
      <div className="balance-card" id="tour-balance">
        <div className="balance-label">Total Margin Balance</div>
        <div className="balance-value">
          {balance === null
            ? <span style={{color:'var(--secondary)',fontFamily:'var(--font-head)',fontSize:14}}>Loading...</span>
            : <>{(parseFloat(balance)||0).toLocaleString('en-US',{minimumFractionDigits:2})} <span style={{fontSize:14,color:'var(--secondary)'}}>USDT</span></>
          }
        </div>
        <div className="balance-sub">
          <div><div className="lbl">24H PNL</div><div className="val price-up">+124.50</div></div>
          <div><div className="lbl">Unrealized</div><div className="val price-up">+38.20</div></div>
        </div>

      </div>
      <div className="panel">
        <div className="panel-header">📋 Order History</div>
        {orders.length===0?<div className="empty-state">No orders yet</div>:(
          <table className="history-table">
            <thead><tr><th>Type</th><th>Asset</th><th>Status</th><th>Size</th></tr></thead>
            <tbody>{orders.slice(0,10).map((o,i)=>(
              <tr key={i}>
                <td><span className={`badge badge-${o.side==='BUY'?'buy':'sell'}`}>{o.side}</span></td>
                <td>{o.symbol}</td>
                <td><span className={`badge ${o.status==='NEW'?'badge-new':'badge-filled'}`}>{o.status}</span></td>
                <td>{o.quantity}</td>
              </tr>
            ))}</tbody>
          </table>
        )}
      </div>
    </div>
  );
}

/* ── STRATEGIES TAB ── */
function StrategiesTab() {
  const cards = [
    {title:'Grid Trading', desc:'Automatically place buy/sell orders at set price intervals'},
    {title:'DCA',          desc:'Dollar cost average into positions over time automatically'},
    {title:'Momentum',     desc:'Follow trend signals and execute on breakout patterns'},
  ];
  return (
    <div>
      <div className="panel-header" style={{marginBottom:16}}>BOT STRATEGIES</div>
      <div className="strategy-cards">
        {cards.map(c=>(
          <div key={c.title} className="strategy-card">
            <div className="strategy-title">{c.title}</div>
            <div className="strategy-desc">{c.desc}</div>
            <span className="badge-soon">COMING SOON</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── SIGNALS TAB ── */
function SignalsTab({orders}) {
  return (
    <div className="panel">
      <div className="panel-header">SIGNAL FEED</div>
      {orders.length===0 ? (
        <div className="signals-empty">
          <span className="dot-pulse"></span>
          Awaiting market signals...
        </div>
      ) : (
        <table className="history-table">
          <thead><tr><th>Time</th><th>Signal</th><th>Pair</th><th>Type</th><th>Size</th><th>Status</th></tr></thead>
          <tbody>{orders.slice(0,15).map((o,i)=>(
            <tr key={i}>
              <td style={{color:'var(--secondary)',fontSize:10}}>{o.timestamp?new Date(o.timestamp).toLocaleTimeString():'--:--'}</td>
              <td><span className={`badge badge-${o.side==='BUY'?'buy':'sell'}`}>{o.side}</span></td>
              <td>{o.symbol}</td>
              <td style={{color:'var(--secondary)'}}>{o.type}</td>
              <td>{o.quantity}</td>
              <td><span className={`badge ${o.status==='NEW'?'badge-new':'badge-filled'}`}>{o.status}</span></td>
            </tr>
          ))}</tbody>
        </table>
      )}
    </div>
  );
}

/* ── SIDEBAR ── (FIX 2: wired icons, active highlight, settings modal) */
const SIDEBAR_ITEMS = [
  {icon:'⚡', label:'Terminal',   tab:'TERMINAL'},
  {icon:'📊', label:'Portfolio',  tab:'PORTFOLIO'},
  {icon:'📋', label:'Strategies', tab:'STRATEGIES'},
  {icon:'💰', label:'Signals',    tab:'SIGNALS'},
  {icon:'⚙️', label:'Settings',   tab:'SETTINGS'},
];

function Sidebar({activeTab, onTabChange, onSettings}) {
  return (
    <div className="sidebar" id="tour-sidebar">
      <div className="logo-sm">Q</div>
      {SIDEBAR_ITEMS.map((item,i)=>(
        <button
          key={i}
          className={activeTab===item.tab?'active':''}
          title={item.label}
          onClick={()=> item.tab==='SETTINGS' ? onSettings() : onTabChange(item.tab)}
        >{item.icon}</button>
      ))}
    </div>
  );
}

/* ── TABBED VIEW ── */
function TabbedView({activeTab, lastPrice, lastOrder, orders, balance, onSubmitOrder}) {
  const tabs = ['TERMINAL','PORTFOLIO','STRATEGIES','SIGNALS'];
  return (
    <>
      <div className="tab-bar">
        {tabs.map(t=><div key={t} className={`tab-item ${activeTab===t?'active':''}`}>{t}</div>)}
      </div>
      <div className="tab-content">
        {activeTab==='TERMINAL'&&<>
          <OrderForm onSubmit={onSubmitOrder} lastPrice={lastPrice}/>
          <CenterPanel lastOrder={lastOrder} orders={orders}/>
        </>}
        {activeTab==='PORTFOLIO'&&<RightPanel balance={balance} orders={orders}/>}
        {activeTab==='STRATEGIES'&&<StrategiesTab/>}
        {activeTab==='SIGNALS'&&<SignalsTab orders={orders}/>}
      </div>
    </>
  );
}

/* ── MAIN APP ── */
function App() {
  const [screen, setScreen]       = useState('startup');
  const [viewMode, setViewMode]   = useState('dashboard');
  const [activeTab, setActiveTab] = useState('TERMINAL');
  const [price, setPrice]         = useState({lastPrice:'0',priceChangePercent:'0'});
  const [balance, setBalance]     = useState(null);   // null = loading, string = loaded
  const [orders, setOrders]       = useState([]);
  const [lastOrder, setLastOrder] = useState(null);
  const [modal, setModal]         = useState(null);
  const [loading, setLoading]     = useState(false);
  const [orderError, setOrderError] = useState(null); // replaces alert()
  const [time, setTime]           = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [showTour, setShowTour]   = useState(false);

  // Clock
  useEffect(()=>{const t=setInterval(()=>setTime(new Date().toLocaleTimeString()),1000);return()=>clearInterval(t)},[]);

  // Price poll
  useEffect(()=>{
    if(screen!=='app') return;
    const poll=()=>api.price().then(r=>{if(r.data) setPrice(r.data)}).catch(()=>{});
    poll();const t=setInterval(poll,3000);return()=>clearInterval(t);
  },[screen]);

  // Balance poll
  useEffect(()=>{
    if(screen!=='app') return;
    const poll=()=>api.balance().then(r=>{if(r.data) setBalance(r.data.availableBalance)}).catch(()=>{});
    poll();const t=setInterval(poll,5000);return()=>clearInterval(t);
  },[screen]);

  // Orders poll
  useEffect(()=>{
    if(screen!=='app') return;
    const poll=()=>api.orders().then(r=>{if(r.data) setOrders(r.data)}).catch(()=>{});
    poll();const t=setInterval(poll,3000);return()=>clearInterval(t);
  },[screen]);

  const isUp       = (parseFloat(price.priceChangePercent) || 0) >= 0;
  const priceColor = isUp?'var(--green)':'var(--red)';
  const arrow      = isUp?'▲':'▼';

  const handleStart = (mode) => {
    setViewMode(mode);
    setScreen('app');
    // Show tour once per session
    if(!sessionStorage.getItem('quantra_tour_done')) {
      setTimeout(()=>setShowTour(true), 400);
    }
  };

  const handleTourDone = () => {
    sessionStorage.setItem('quantra_tour_done','true');
    setShowTour(false);
  };

  const handleSwitchLayout = () => {
    sessionStorage.removeItem('quantra_tour_done');
    setShowSettings(false);
    setScreen('startup');
    setActiveTab('TERMINAL');
  };

  // ── Tab switching: ⚡ Terminal → dashboard view, all others → tabbed view
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === 'TERMINAL') {
      setViewMode('dashboard');
    } else {
      setViewMode('tabbed');
    }
  };

  const handleSubmitOrder = (body) => { setOrderError(null); setModal(body); };
  const handleConfirm = async () => {
    setLoading(true);
    setOrderError(null);
    try {
      const r = await api.placeOrder(modal);
      setLastOrder(r.data);
      setOrders(prev=>[r.data,...prev]);
      setModal(null);
    } catch(e) {
      setModal(null);
      setOrderError(e.message || 'Order failed. Check the activity log.');
    }
    finally {setLoading(false);}
  };

  // Sidebar active = activeTab, but when in dashboard mode treat it as TERMINAL
  const sidebarActive = viewMode === 'dashboard' ? 'TERMINAL' : activeTab;

  if(screen==='startup') return <StartupScreen onStart={handleStart}/>;

  return (
    <div className="app">
      <Sidebar activeTab={sidebarActive} onTabChange={handleTabChange} onSettings={()=>setShowSettings(true)}/>
      <div className="main-area">
        <div className="navbar">
          <div className="nav-brand">QUANTRA</div>
          <div className="nav-price" id="tour-price" style={{color:priceColor}}>
            {price.symbol||'BTCUSDT'}&nbsp;&nbsp;
            {price.lastPrice==='0'
              ? <span style={{color:'var(--secondary)'}}>Loading...</span>
              : <>{(parseFloat(price.lastPrice)||0).toLocaleString('en-US',{minimumFractionDigits:2})}&nbsp;USDT</>}
            &nbsp;&nbsp;
            <span className="pct">{arrow} {isUp?'+':''}{(parseFloat(price.priceChangePercent)||0).toFixed(2)}%</span>
          </div>
          <div className="nav-time">{time}</div>
        </div>
        {orderError && (
          <div className="order-error-bar">
            <span className="error-icon">⚠</span>
            <span>{orderError}</span>
            <button className="error-dismiss" onClick={()=>setOrderError(null)}>✕</button>
          </div>
        )}
        {viewMode==='dashboard'?(
          <div className="dashboard">
            <OrderForm onSubmit={handleSubmitOrder} lastPrice={price.lastPrice}/>
            <CenterPanel lastOrder={lastOrder} orders={orders}/>
            <RightPanel balance={balance} orders={orders}/>
          </div>
        ):(
          <TabbedView activeTab={activeTab} lastPrice={price.lastPrice} lastOrder={lastOrder} orders={orders} balance={balance} onSubmitOrder={handleSubmitOrder}/>
        )}
      </div>
      <ConfirmModal order={modal} onConfirm={handleConfirm} onCancel={()=>setModal(null)} loading={loading}/>
      {showSettings && <SettingsModal onClose={()=>setShowSettings(false)} onSwitchLayout={handleSwitchLayout}/>}
      {showTour && <Tour onDone={handleTourDone}/>}
      <div className="status-bar">
        <span><span className="dot"></span>CORE_STABLE</span>
        <span>LATENCY: 12ms</span>
        <span>BUILD: v1.4.2-neon</span>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
