import React, { useState } from "react";

function TicketAccordion({ ticket }) {

  const [open, setOpen] = useState(false);

  return (

    <div style={{
      border: "1px solid gray",
      marginBottom: "10px",
      padding: "10px"
    }}>

      <div
        style={{ cursor: "pointer" }}
        onClick={() => setOpen(!open)}
      >

        <b>{ticket.title}</b> - {ticket.status}

      </div>

      {open && (

        <div style={{ marginTop: "10px" }}>

          <p><b>Issue ID:</b> {ticket.issueId}</p>

          <p><b>Test ID:</b> {ticket.testId}</p>

          <p><b>Description:</b> {ticket.description}</p>

          <p><b>Jira Ticket:</b> {ticket.jiraTicketId || "Not Created"}</p>

          <p><b>Developer:</b> {ticket.assignedDeveloper}</p>

        </div>

      )}

    </div>

  );

}

export default TicketAccordion;