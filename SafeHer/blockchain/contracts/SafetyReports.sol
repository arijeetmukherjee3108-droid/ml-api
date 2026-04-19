// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

contract SafetyReports {

    enum IncidentType { Harassment, Stalking, Suspicious, Other }

    struct Report {
        bytes32 locationHash;
        IncidentType incidentType;
        bytes32 contentHash; // Anchors Suspect Name & Evidence URL securely
        uint256 timestamp;
        bool isActive;
        bytes32 resolutionToken;
    }

    mapping(uint256 => Report) public reports;
    uint256 public reportCount;

    event ReportFiled(
        uint256 indexed reportId,
        bytes32 locationHash,
        IncidentType incidentType,
        bytes32 contentHash,
        uint256 timestamp
    );

    event ReportResolved(uint256 indexed reportId);

    function fileReport(
        bytes32 _locationHash, 
        IncidentType _incidentType,
        bytes32 _contentHash,
        bytes32 _resolutionToken
    ) public {
        require(_locationHash != bytes32(0), "Invalid location");
        require(uint256(_incidentType) <= uint256(IncidentType.Other), "Invalid incident type");

        reportCount++;

        reports[reportCount] = Report(
            _locationHash,
            _incidentType,
            _contentHash,
            block.timestamp,
            true,
            _resolutionToken
        );

        emit ReportFiled(
            reportCount, 
            _locationHash, 
            _incidentType, 
            _contentHash, 
            block.timestamp
        );
    }

    function markResolved(uint256 _reportId, string memory _secret) public {
        require(_reportId > 0 && _reportId <= reportCount, "Report does not exist");
        require(reports[_reportId].isActive, "Already resolved");
        // Verify that the hash of the provided secret matches the stored token
        require(keccak256(abi.encodePacked(_secret)) == reports[_reportId].resolutionToken, "Unauthorized: Invalid password");

        reports[_reportId].isActive = false;

        emit ReportResolved(_reportId);
    }

    function getReport(uint256 _reportId) public view returns (Report memory) {
        require(_reportId > 0 && _reportId <= reportCount, "Report does not exist");
        return reports[_reportId];
    }
}