import React, { useEffect, useState } from "react";
import IssueCard from "../components/IssueCard";
import issueService from "../services/issueService";

function IssueListPage() {

  const [issues, setIssues] = useState([]);

  useEffect(() => {
    loadIssues();
  }, []);

  const loadIssues = async () => {

    try {

      const data = await issueService.getIssues();

      setIssues(data);

    } catch (error) {

      console.error("Error loading issues", error);

    }

  };

  return (

    <div style={{ padding: "20px" }}>

      <h2>Issue Review</h2>

      {issues.map(issue => (

        <IssueCard
          key={issue._id}
          issue={issue}
          refresh={loadIssues}
        />

      ))}

    </div>

  );

}

export default IssueListPage;