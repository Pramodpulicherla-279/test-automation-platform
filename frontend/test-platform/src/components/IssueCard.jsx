import React, { useState } from "react";
import EditTicketModal from "./EditTicketModal";
import issueService from "../services/issueService";

function IssueCard({ issue, refresh }) {

  const [openModal, setOpenModal] = useState(false);

  const createTicket = async () => {

    try {

      await issueService.createTicket(issue._id);

      alert("Jira ticket created successfully");

      refresh();

    } catch (error) {

      console.error(error);

    }

  };

  return (

    <div style={{
      border: "1px solid #ddd",
      padding: "15px",
      marginBottom: "10px"
    }}>

      <h4>{issue.title}</h4>

      <p>{issue.description}</p>

      <p><b>Issue ID:</b> {issue.issueId}</p>

      <p><b>Test ID:</b> {issue.testId}</p>

      <p><b>Developer:</b> {issue.assignedDeveloper || "Not Assigned"}</p>

      <button onClick={() => setOpenModal(true)}>
        Edit
      </button>

      <button onClick={createTicket}>
        Create Ticket
      </button>

      {openModal && (

        <EditTicketModal
          issue={issue}
          close={() => setOpenModal(false)}
          refresh={refresh}
        />

      )}

    </div>

  );

}

export default IssueCard;