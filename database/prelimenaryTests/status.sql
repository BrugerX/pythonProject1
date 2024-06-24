select meta.lid,auction_history.is_closed
from
               meta,auction_history
inner join (select max(latest_bid_timestamp) as ts,lid
            from auction_history group by lid) m_ah on m_ah.lid = auction_history.lid and m_ah.ts = auction_history.latest_bid_timestamp
order by
    is_closed asc;