import React, { useEffect, useState } from "react";
import TicketAccordion from "../components/TicketAccordion";
import issueService from "../services/issueService";

function TicketHistoryPage() {

  const [tickets, setTickets] = useState([]);

  useEffect(() => {

    loadHistory();

  }, []);

  const loadHistory = async () => {

    const data = await issueService.getHistory();

    setTickets(data);

  };

  return (

    <div style={{ padding: "20px" }}>

      <h2>Ticket History</h2>

      {tickets.map(ticket => (

        <TicketAccordion
          key={ticket._id}
          ticket={ticket}
        />

      ))}

    </div>

  );

}

export default TicketHistoryPage;