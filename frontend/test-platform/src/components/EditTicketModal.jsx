import React, { useState } from "react";
import issueService from "../services/issueService";

function EditTicketModal({ issue, close, refresh }) {

  const [title, setTitle] = useState(issue.title);
  const [description, setDescription] = useState(issue.description);
  const [developer, setDeveloper] = useState(issue.assignedDeveloper || "");

  const saveChanges = async () => {

    try {

      await issueService.updateIssue(issue._id, {
        title,
        description,
        assignedDeveloper: developer
      });

      alert("Issue updated successfully");

      refresh();

      close();

    } catch (error) {

      console.error(error);

    }

  };

  return (

    <div style={{
      background: "#f0f0f0",
      padding: "20px",
      marginTop: "10px"
    }}>

      <h3>Edit Issue</h3>

      <p>Issue ID: {issue.issueId}</p>

      <p>Test ID: {issue.testId}</p>

      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />

      <br/><br/>

      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />

      <br/><br/>

      <input
        placeholder="Developer"
        value={developer}
        onChange={(e) => setDeveloper(e.target.value)}
      />

      <br/><br/>

      <button onClick={saveChanges}>
        Save
      </button>

      <button onClick={close}>
        Cancel
      </button>

    </div>

  );

}

export default EditTicketModal;