/**
 * Navigation column component and its subcomponents. Used to control navigation
 * from a current selected branch node down to its child nodes.
 */
import React from 'react';
import _ from 'lodash';
import { ListGroup, ListGroupItem } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlay, faRedo } from '@fortawesome/free-solid-svg-icons';
import { Link } from "react-router-dom";
import { StyleSheet, css } from "aphrodite";

import { LIGHT_GREY, MEDIUM_GREY, COLWIDTH, BranchNode, LeafNode } from "./Common";

interface NavColumnProps {
  childBranches: { [key: string]: BranchNode },
  childLeaves: { [key: string]: LeafNode },
  selectedLeafID: string | null,
  selection: Array<string>,
  handleTestRun: (nodeid: string) => void,
}

/**
 * NavColumn component: renders the current navigation selection.
 * @param props Component props
 */
export const NavColumn = (props: NavColumnProps) => {
  if (_.isEmpty(props.childBranches) && _.isEmpty(props.childLeaves)) {
    return <div className={css(styles.navColumn)} />;
  }

  return (
    <div className={css(styles.navColumn)}>
      <ListGroup>
        <NavBranchEntries
          childBranches={props.childBranches}
          selection={props.selection}
          handleTestRun={props.handleTestRun}
        />
        <NavLeafEntries
          childLeaves={props.childLeaves}
          handleTestRun={props.handleTestRun}
          selectedLeafID={props.selectedLeafID}
        />
      </ListGroup>
    </div>
  );
};

interface NavBranchEntriesProps {
  childBranches: { [key: string]: BranchNode },
  selection: Array<string>,
  handleTestRun: (nodeid: string) => void,
}

/**
 * Render entries in the nav column for branch nodes that are children of the
 * currently selected node.
 * @param props Render props
 */
const NavBranchEntries = (props: NavBranchEntriesProps) => {
  const childBranchIDs = Object.keys(props.childBranches);
  return (
    <>
      {
        childBranchIDs.map(
          (short_id: string) => {
            const childNode = props.childBranches[short_id];
            console.log(props.selection);
            const linkAddr = "/" + props.selection
              .concat([short_id])
              .map(encodeURIComponent)
              .join("/");
            console.log(linkAddr);
            console.log("updated");

            return (
              <ListGroupItem
                key={short_id}
                className={
                  css(
                    getNavEntryStyle(childNode.status),
                    styles.navEntryCommon,
                  )
                }
              >
                <span className={css(styles.navLabel)}>
                  <Link
                    to={linkAddr}
                  >
                    {short_id}
                  </Link>
                </span>
                <NavEntryIcon
                  nodeid={childNode.nodeid}
                  status={childNode.status}
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

interface NavLeafEntriesProps {
  childLeaves: { [key: string]: LeafNode },
  selectedLeafID: string | null,
  handleTestRun: (nodeid: string) => void,
}

/**
 * Render entries in the navigation column for child leaves of the currently
 * selected node.
 * @param props Render props
 */
const NavLeafEntries = (props: NavLeafEntriesProps) => {
  const childLeafIDs = Object.keys(props.childLeaves);

  return (
    <>
      {
        childLeafIDs.map(
          (short_id: string) => {
            const label = (short_id === props.selectedLeafID) ?
              short_id :
              (
                <Link
                  to={`?selectedLeaf=${encodeURIComponent(short_id)}`}
                >
                  {short_id}
                </Link>
              );
            const childLeaf = props.childLeaves[short_id];

            return (
              <ListGroupItem
                key={short_id}
                className={
                  css(
                    getNavEntryStyle(
                      props.childLeaves[short_id].status
                    ),
                    styles.navEntryCommon,
                  )
                }
              >
                <span className={css(styles.navLabel)}>{label}</span>
                <NavEntryIcon
                  nodeid={childLeaf.nodeid}
                  status={childLeaf.status}
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
    transition: 'color 0.3s ease-out 0s',
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
