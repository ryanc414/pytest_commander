/**
 * Navigation column component and its subcomponents. Used to control navigation
 * from a current selected branch node down to its child nodes.
 */
import React from 'react';
import { ListGroup, ListGroupItem } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlay, faRedo } from '@fortawesome/free-solid-svg-icons';
import { Link } from "react-router-dom";
import { StyleSheet, css } from "aphrodite";

import { LIGHT_GREY, MEDIUM_GREY, COLWIDTH, BranchNode } from "./Common";

interface NavColumnProps {
  selectedBranch: BranchNode | null,
  selectedLeafID: string | null,
  selection: Array<string>,
  handleTestRun: (nodeid: string) => void,
}

/**
 * NavColumn component: renders the current navigation selection.
 * @param props Component props
 */
export const NavColumn = (props: NavColumnProps) => {
  if (!props.selectedBranch) {
    return <span>Loading...</span>;
  }

  return (
    <div className={css(styles.navColumn)}>
      <ListGroup>
        <NavBranchEntries
          selectedBranch={props.selectedBranch}
          selection={props.selection}
          handleTestRun={props.handleTestRun}
        />
        <NavLeafEntries
          selectedBranch={props.selectedBranch}
          handleTestRun={props.handleTestRun}
          selectedLeafID={props.selectedLeafID}
        />
      </ListGroup>
    </div>
  );
};

interface NavBranchEntriesProps {
  selectedBranch: BranchNode,
  selection: Array<string>,
  handleTestRun: (nodeid: string) => void,
}

/**
 * Render entries in the nav column for branch nodes that are children of the
 * currently selected node.
 * @param props Render props
 */
const NavBranchEntries = (props: NavBranchEntriesProps) => {
  const childBranches = Object.keys(props.selectedBranch.child_branches);
  return (
    <>
      {
        childBranches.map(
          (nodeid: string) => (
            <ListGroupItem
              key={nodeid}
              className={
                css(
                  getNavEntryStyle(
                    props.selectedBranch.child_branches[nodeid].status
                  ),
                  styles.navEntryCommon,
                )
              }
            >
              <span className={css(styles.navLabel)}>
                <Link
                  to={
                    props.selection
                      .concat([nodeid])
                      .map(encodeURIComponent)
                      .join("/")
                  }
                >
                  {nodeid}
                </Link>
              </span>
              <NavEntryIcon
                nodeid={nodeid}
                status={props.selectedBranch.child_branches[nodeid].status}
                handleTestRun={props.handleTestRun}
              />
            </ListGroupItem>
          )
        )
      }
    </>
  );
};

interface NavLeafEntriesProps {
  selectedBranch: BranchNode,
  selectedLeafID: string | null,
  handleTestRun: (nodeid: string) => void,
}

/**
 * Render entries in the navigation column for child leaves of the currently
 * selected node.
 * @param props Render props
 */
const NavLeafEntries = (props: NavLeafEntriesProps) => {
  const childLeaves = Object.keys(props.selectedBranch.child_leaves);

  return (
    <>
      {
        childLeaves.map(
          (nodeid: string) => {
            const label = (nodeid === props.selectedLeafID) ?
              nodeid :
              (
                <Link
                  to={`?selectedLeaf=${encodeURIComponent(nodeid)}`}
                >
                  {nodeid}
                </Link>
              );

            return (
              <ListGroupItem
                key={nodeid}
                className={
                  css(
                    getNavEntryStyle(
                      props.selectedBranch.child_leaves[nodeid].status
                    ),
                    styles.navEntryCommon,
                  )
                }
              >
                <span className={css(styles.navLabel)}>{label}</span>
                <NavEntryIcon
                  nodeid={nodeid}
                  status={props.selectedBranch.child_leaves[nodeid].status}
                  handleTestRun={props.handleTestRun}
                />
              </ListGroupItem>
            );
          }
        )
      }
    </>
  );
};

interface NavEntryIconProps {
  nodeid: string,
  status: string,
  handleTestRun: (nodeid: string) => void,
}

const NavEntryIcon = (props: NavEntryIconProps) => {
  switch (props.status) {
    case "running":
      return (
        <FontAwesomeIcon
          icon={faRedo}
          spin
        />
      );

    default:
      return (
        <FontAwesomeIcon
          icon={faPlay}
          onClick={(e: React.MouseEvent) => {
            e.stopPropagation();
            props.handleTestRun(props.nodeid);
          }}
          className={css(styles.runButton)}
        />
      );
  }
};

/**
 * 
 * @param status 
 */
const getNavEntryStyle = (status: string) => {
  switch (status) {
    case "passed":
      return styles.navEntryPassed;

    case "failed":
      return styles.navEntryFailed;

    default:
      return styles.navEntryDefault;
  }
}

const styles = StyleSheet.create({
  navColumn: {
    height: "100%",
    width: COLWIDTH,
    position: "fixed",
    "z-index": 1,
    "top": 0,
    "left": 0,
    "overflow-x": "hidden",
    padding: "20px",
    background: LIGHT_GREY,
  },
  navLabel: {
    "text-overflow": "ellipsis",
    "white-space": "nowrap",
    fontSize: "small",
    "max-width": "90%",
  },
  runButton: {
    cursor: 'pointer',
    color: 'black',
    transition: 'all 0.3s ease-out 0s',
    ':hover': {
      color: LIGHT_GREY
    }
  },
  navEntryPassed: { background: "#c0ffbf" },
  navEntryFailed: { background: "#ff7a7a" },
  navEntryDefault: { background: MEDIUM_GREY },
  navEntryCommon: {
    display: "flex",
    "justify-content": "space-between",
    "align-items": "center",
  }
});
